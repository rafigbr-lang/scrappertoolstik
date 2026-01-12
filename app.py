import streamlit as st
import pandas as pd
import asyncio
from TikTokApi import TikTokApi
import os
import subprocess
import io
from datetime import datetime

# --- FIX PERMANEN UNTUK STREAMLIT CLOUD ---
# Mengatur folder cache Playwright agar konsisten
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "0" 

def install_playwright():
    try:
        # Mengunduh chromium ke dalam folder environment
        subprocess.run(["python", "-m", "playwright", "install", "chromium"], check=True)
        subprocess.run(["python", "-m", "playwright", "install-deps"], check=True)
    except Exception as e:
        st.error(f"Instalasi Browser Gagal: {e}")

# Cek instalasi saat startup
if 'setup_done' not in st.session_state:
    with st.spinner("Sedang mengunduh browser Chromium... Mohon tunggu sebentar."):
        install_playwright()
        st.session_state['setup_done'] = True

# --- KONFIGURASI APP ---
st.set_page_config(page_title="TikTok Data Scalper", page_icon="📊")

MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if not info or "author" not in info:
            return {"video_url": url, "error": "Video Private/Token Expired"}
        
        stats = info.get("stats", {})
        return {
            "video_url": url,
            "author": info.get("author", {}).get("uniqueId"),
            "views": stats.get("playCount", 0),
            "likes": stats.get("diggCount", 0),
            "comments": stats.get("commentCount", 0),
            "shares": stats.get("shareCount", 0),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --- UI ---
st.title("📱 TikTok Data Scalper")

uploaded_file = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    if "video_url" in df_input.columns:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"Ditemukan {len(urls)} URL")

        if st.button("🚀 Jalankan Scraper"):
            results = []
            progress_bar = st.progress(0)

            async def main():
                async with TikTokApi() as api:
                    # Inisialisasi session tanpa parameter yang sering berubah
                    await api.create_sessions(ms_tokens=[MS_TOKEN], num_sessions=1, sleep_after=3)
                    
                    for idx, url in enumerate(urls):
                        data = await get_video_info(url, api)
                        results.append(data)
                        progress_bar.progress((idx + 1) / len(urls))
                        await asyncio.sleep(2)
                return results

            with st.spinner("Proses scraping sedang berjalan..."):
                final_res = asyncio.run(main())
            
            df_res = pd.DataFrame(final_res)
            st.dataframe(df_res)

            # Tombol Download
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_res.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Hasil Excel",
                data=output.getvalue(),
                file_name="hasil_tiktok.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.error("Kolom 'video_url' tidak ditemukan!")
