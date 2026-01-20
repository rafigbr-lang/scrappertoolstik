import streamlit as st
from TikTokApi import TikTokApi
import pandas as pd
import asyncio
import os
import sys
import logging
from datetime import datetime
import io
import subprocess

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📊", layout="wide")

@st.cache_resource
def setup_browser():
    try:
        # Menginstal browser Playwright
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Gagal menginstal browser: {e}")
        return False

# Jalankan setup browser
browser_ready = setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        return int(value) if value is not None else 0
    except:
        return 0

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        
        if not info:
            return {"video_url": url, "error": "Data tidak ditemukan (Cek URL/Token)"}

        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        video_data = info.get("video", {})

        raw_time = info.get("createTime", 0)
        formatted_time = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S") if raw_time else "N/A"

        return {
            "video_url": url,
            "create_time": formatted_time,
            "video_id": info.get("id") or video_data.get("id"),
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "follower_count": safe_int(author_stats.get("followerCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "comment_count": safe_int(stats.get("commentCount")),
            "play_count": safe_int(stats.get("playCount")),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Scraper Engine ---------
async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        async with TikTokApi() as api:
            # Headless=True wajib untuk Streamlit Cloud
            await api.create_sessions(
                ms_tokens=[ms_token], 
                num_sessions=1, 
                sleep_after=5, 
                browser="chromium",
                headless=True
            )

            for idx, url in enumerate(video_urls):
                status_text.write(f"⏳ Memproses {idx+1}/{len(video_urls)}: {url}")
                data = await get_video_info(url, api)
                
                if "error" in data:
                    failed.append(data)
                else:
                    results.append(data)
                
                progress_bar.progress((idx + 1) / len(video_urls))
                await asyncio.sleep(2) 
    except Exception as e:
        st.error(f"Gagal inisialisasi session: {e}")
            
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Dashboard")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password")
    st.info("Gunakan MS Token terbaru dari browser.")

uploaded_file = st.file_uploader("Upload Input Excel", type=["xlsx"])

if uploaded_file:
    df_in = pd.read_excel(uploaded_file)
    if "video_url" in df_in.columns:
        urls = df_in["video_url"].dropna().tolist()
        st.success(f"{len(urls)} video ditemukan.")
        
        if st.button("Mulai Scraping"):
            if not token:
                st.warning("Mohon isi MS Token.")
            else:
                res, fail = asyncio.run(run_scraper(urls, token))
                
                # Cek apakah ada data untuk dibuatkan Excel
                if not res and not fail:
                    st.error("Gagal mengambil data sama sekali. Periksa log atau ganti MS Token.")
                else:
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        # Hanya buat sheet jika ada datanya
                        if res:
                            pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Berhasil")
                        if fail:
                            pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Gagal")
                        # Jika keduanya kosong, tulis satu sheet placeholder agar tidak error
                        if not res and not fail:
                            pd.DataFrame([{"info": "No data"}]).to_excel(writer, index=False, sheet_name="Empty")
                    
                    st.divider()
                    st.download_button("📥 Download Hasil", output.getvalue(), file_name="tiktok_results.xlsx")
                    if res:
                        st.dataframe(pd.DataFrame(res))
    else:
        st.error("Kolom 'video_url' tidak ditemukan!")
