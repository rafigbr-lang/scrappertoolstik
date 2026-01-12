import streamlit as st
import pandas as pd
import asyncio
from TikTokApi import TikTokApi
import os
from datetime import datetime
import io
import subprocess

# --- PERBAIKAN: AUTO INSTALLER BROWSER ---
# Fungsi ini memastikan Playwright mendownload browser saat dijalankan di server
def install_playwright():
    try:
        # Cek apakah browser sudah terinstal
        import playwright
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Gagal menginstal Playwright Browser: {e}")

# Jalankan instalasi di awal
if 'playwright_installed' not in st.session_state:
    with st.spinner("Menginisialisasi mesin browser (ini hanya sekali)..."):
        install_playwright()
        st.session_state['playwright_installed'] = True

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="TikTok Data Scalper", page_icon="📊", layout="wide")

# Masukkan ms_token terbaru Anda
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --- HELPER: SCRAPING ---
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if not info or "author" not in info:
            return {"video_url": url, "error": "Data tidak ditemukan / Token expired"}

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
st.markdown("Upload file Excel dengan kolom **`video_url`** untuk mendapatkan data statistik.")

uploaded_file = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan di file Excel!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"📂 Berhasil membaca {len(urls)} link video.")
        
        if st.button("🚀 Mulai Scraping"):
            results = []
            failed = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def run_scraper():
                try:
                    async with TikTokApi() as api:
                        await api.create_sessions(
                            ms_tokens=[MS_TOKEN], 
                            num_sessions=1, 
                            sleep_after=3
                        )
                        
                        for idx, url in enumerate(urls):
                            status_text.text(f"Memproses ({idx+1}/{len(urls)}): {url}")
                            data = await get_video_info(url, api)
                            
                            if "error" in data:
                                failed.append(data)
                            else:
                                results.append(data)
                            
                            progress_bar.progress((idx + 1) / len(urls))
                            await asyncio.sleep(1.5) # Jeda agar tidak diblokir
                            
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menjalankan scraper: {e}")
                
                return results, failed

            with st.spinner("Harap tunggu, sedang mengambil data..."):
                # Menjalankan loop async di dalam Streamlit
                success_data, failed_data = asyncio.run(run_scraper())
            
            st.divider()
            
            if success_data:
                df_final = pd.DataFrame(success_data)
                st.subheader("📊 Hasil Scraping")
                st.dataframe(df_final)
                
                # Download Button
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Success')
                    if failed_data:
                        pd.DataFrame(failed_data).to_excel(writer, index=False, sheet_name='Failed')
                
                st.download_button(
                    label="📥 Download Hasil (.xlsx)",
                    data=buffer.getvalue(),
                    file_name=f"tiktok_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            if failed_data:
                with st.expander("Lihat URL yang Gagal"):
                    st.write(pd.DataFrame(failed_data))
