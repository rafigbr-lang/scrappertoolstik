import streamlit as st
import pandas as pd
import asyncio
from TikTokApi import TikTokApi
import os
from datetime import datetime
import io

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="TikTok Data Scalper", page_icon="📊")

# Masukkan ms_token kamu di sini
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info:
            return {"video_url": url, "error": "Data tidak ditemukan (mungkin video private/deleted)"}

        return {
            "video_url": url,
            "create_time": info.get("createTime"),
            "author_name": info.get("author", {}).get("nickname"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "share_count": int(info.get("stats", {}).get("shareCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Streamlit UI ---------
st.title("📱 TikTok Video Scraper")
st.markdown("Upload file Excel berisi kolom `video_url` untuk mengambil data statistik.")

uploaded_file = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.info(f"Total URL terdeteksi: {len(urls)}")

        if st.button("Mulai Scraping"):
            results = []
            
            # Progress Bar Streamlit
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def run_scraper():
                async with TikTokApi() as api:
                    await api.create_sessions(ms_tokens=[MS_TOKEN], num_sessions=1, sleep_after=2)
                    
                    for idx, url in enumerate(urls):
                        status_text.text(f"Memproses {idx+1}/{len(urls)}: {url}")
                        data = await get_video_info(url, api)
                        results.append(data)
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(urls))
                return results

            # Jalankan loop async
            final_data = asyncio.run(run_scraper())
            
            # Tampilkan Hasil
            df_result = pd.DataFrame(final_data)
            st.success("✅ Scraping Selesai!")
            st.dataframe(df_result)

            # Persiapan Download (Menggunakan Buffer agar tidak perlu simpan file di server)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_result.to_excel(writer, index=False, sheet_name='Hasil Scraping')
            
            st.download_button(
                label="📥 Download Hasil Excel",
                data=buffer.getvalue(),
                file_name=f"hasil_scraping_{datetime.now().strftime('%d%m%y_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
