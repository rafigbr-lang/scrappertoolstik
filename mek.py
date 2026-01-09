import streamlit as st
from TikTokApi import TikTokApi
import pandas as pd
import asyncio
import os
import logging
from datetime import datetime
import io

# Konfigurasi Halaman Streamlit
st.set_page_config(page_title="TikTok Video Scraper", page_icon="📊")

# Suppress TikTokApi logger
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)

# Masukkan ms_token kamu di sini (Bisa diletakkan di st.secrets untuk keamanan)
DEFAULT_MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info or "authorStats" not in info or "stats" not in info:
            raise ValueError("Missing author or stats data")

        return {
            "video_url": url,
            "create_time": info.get("createTime"),
            "video_id": info.get("video", {}).get("id"),
            "author_id": info.get("author", {}).get("id"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "nickname": info.get("author", {}).get("nickname"),
            "music_title": info.get("music", {}).get("title"),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "share_count": int(info.get("stats", {}).get("shareCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Main Scraper Logic ---------
async def run_scraper(video_urls, token):
    results = []
    failed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[token],
            num_sessions=1,
            sleep_after=2,
            browser="chromium" # Streamlit Cloud mendukung chromium via buildpack
        )

        for idx, url in enumerate(video_urls):
            status_text.text(f"Scraping video {idx+1} dari {len(video_urls)}...")
            data = await get_video_info(url, api)
            
            if "error" not in data:
                results.append(data)
            else:
                failed.append(data)
            
            progress_bar.progress((idx + 1) / len(video_urls))
            
    return results, failed

# --------- Streamlit UI ---------
def main():
    st.title("🚀 TikTok Scalper Scraper")
    st.write("Upload file Excel yang berisi kolom `video_url` untuk mengambil data.")

    # Sidebar untuk Token
    with st.sidebar:
        st.header("Settings")
        token = st.text_input("MS Token", value=DEFAULT_MS_TOKEN, type="password")
        st.info("Token ini diperlukan untuk otentikasi TikTok.")

    uploaded_file = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        df_input = pd.read_excel(uploaded_file)
        
        if "video_url" not in df_input.columns:
            st.error("Error: Kolom 'video_url' tidak ditemukan!")
            return

        urls = df_input["video_url"].dropna().tolist()
        st.success(f"Ditemukan {len(urls)} URL video.")

        if st.button("Mulai Scraping"):
            # Menjalankan loop asyncio di dalam Streamlit
            results, failed = asyncio.run(run_scraper(urls, token))

            # Tampilkan Hasil
            st.divider()
            st.subheader("Hasil Scraping")
            
            # Buat file Excel di memori untuk didownload
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if results:
                    pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Success")
                if failed:
                    pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Failed")
            
            st.download_button(
                label="📥 Download Hasil Scraping",
                data=output.getvalue(),
                file_name=f"scraped_tiktok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            if results:
                st.write("Preview Data Berhasil:")
                st.dataframe(pd.DataFrame(results).head())
            
            if failed:
                st.warning(f"Gagal mengambil {len(failed)} video.")
                st.write(pd.DataFrame(failed))

if __name__ == "__main__":
    main()
