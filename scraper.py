import streamlit as st
import pandas as pd
import asyncio
from TikTokApi import TikTokApi
import os
from datetime import datetime
import io
import sys

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="TikTok Data Scalper", page_icon="📊", layout="wide")

# Masukkan ms_token kamu di sini
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --- HELPER: SCRAPING ---
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if not info or "author" not in info:
            return {"video_url": url, "error": "Video tidak ditemukan/Private"}

        # Mengambil data statistik
        stats = info.get("stats", {})
        author_stats = info.get("authorStats", {})
        
        return {
            "video_url": url,
            "video_id": info.get("id"),
            "create_time": datetime.fromtimestamp(info.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
            "author_unique_id": info.get("author", {}).get("uniqueId"),
            "author_nickname": info.get("author", {}).get("nickname"),
            "follower_count": int(author_stats.get("followerCount", 0)),
            "play_count": int(stats.get("playCount", 0)),
            "like_count": int(stats.get("diggCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "share_count": int(stats.get("shareCount", 0)),
            "collect_count": int(stats.get("collectCount", 0)),
            "hashtags": ", ".join([h["hashtagName"] for h in info.get("textExtra", []) if h.get("hashtagName")]),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --- UI STREAMLIT ---
st.title("📱 TikTok Data Scalper Professional")
st.markdown("""
Aplikasi ini mengambil data statistik video TikTok secara otomatis dari file Excel.
1. Upload file Excel yang memiliki kolom **`video_url`**.
2. Klik tombol 'Mulai Scraping'.
3. Download hasilnya.
""")

uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Load data awal
    df_input = pd.read_excel(uploaded_file)
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan dalam file!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"📂 File terbaca! Menemukan {len(urls)} link video.")
        
        if st.button("🚀 Mulai Scraping"):
            results = []
            failed = []
            
            # Progress Bar
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def run_scraper():
                try:
                    async with TikTokApi() as api:
                        # Inisialisasi session dengan argumen untuk server
                        await api.create_sessions(
                            ms_tokens=[MS_TOKEN], 
                            num_sessions=1, 
                            sleep_after=2,
                            browser_args=["--no-sandbox", "--disable-dev-shm-usage"]
                        )
                        
                        for idx, url in enumerate(urls):
                            status_text.text(f"Processing ({idx+1}/{len(urls)}): {url}")
                            data = await get_video_info(url, api)
                            
                            if "error" in data:
                                failed.append(data)
                            else:
                                results.append(data)
                            
                            # Update progress
                            progress_bar.progress((idx + 1) / len(urls))
                            
                except Exception as e:
                    st.error(f"Terjadi kesalahan pada koneksi TikTok: {e}")
                
                return results, failed

            # Jalankan Async Loop
            with st.spinner("Harap tunggu, sedang mengambil data..."):
                success_data, failed_data = asyncio.run(run_scraper())
            
            # --- HASIL ---
            st.divider()
            st.subheader("📊 Hasil Scraping")
            
            if success_data:
                df_final = pd.DataFrame(success_data)
                st.dataframe(df_final, use_container_width=True)
                
                # Download Button
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Success')
                    if failed_data:
                        pd.DataFrame(failed_data).to_excel(writer, index=False, sheet_name='Failed')
                
                st.download_button(
                    label="📥 Download Hasil (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"tiktok_scraped_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("Tidak ada data yang berhasil diambil. Cek koneksi atau token.")

            if failed_data:
                with st.expander("Lihat URL yang Gagal"):
                    st.table(pd.DataFrame(failed_data))
