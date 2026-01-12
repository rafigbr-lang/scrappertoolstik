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

# --- SETUP ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Fix", page_icon="✅", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- HELPER FUNGSI AMAN ---
def safe_int(value):
    """Mengonversi nilai ke integer secara aman agar tidak error 'str object'"""
    try:
        if value is None: return 0
        return int(value)
    except (ValueError, TypeError):
        return 0

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        
        if not info:
            return {"video_url": url, "error": "Tidak ada respon dari TikTok"}

        # Ambil data statistik dengan konversi aman
        stats = info.get("stats", {})
        author_stats = info.get("authorStats", {})
        
        # Konversi waktu buat (createTime bisa berupa string atau int dari TikTok)
        raw_time = info.get("createTime", 0)
        try:
            create_time_str = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
        except:
            create_time_str = "Unknown"

        return {
            "video_url": url,
            "create_time": create_time_str,
            "nickname": info.get("author", {}).get("nickname", "N/A"),
            "unique_id": info.get("author", {}).get("uniqueId", "N/A"),
            "follower_count": safe_int(author_stats.get("followerCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "comment_count": safe_int(stats.get("commentCount")),
            "play_count": safe_int(stats.get("playCount")),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": f"Logic Error: {str(e)}"}

# --------- Scraper Engine ---------
async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")

        for idx, url in enumerate(video_urls):
            status_text.write(f"⏳ Memproses {idx+1}/{len(video_urls)}...")
            data = await get_video_info(url, api)
            
            if "error" in data:
                failed.append(data)
            else:
                results.append(data)
            
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(2) # Jeda agar tidak dianggap bot agresif
            
    return results, failed

# --------- UI ---------
st.title("🚀 TikTok Scalper Dashboard (Fixed Version)")

with st.sidebar:
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if "video_url" in df.columns:
        urls = df["video_url"].dropna().tolist()
        if st.button("Mulai Scrape"):
            res, fail = asyncio.run(run_scraper(urls, token))
            
            # Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if res: pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Berhasil")
                if fail: pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Gagal")
            
            st.success("Selesai!")
            st.download_button("📥 Download Hasil", output.getvalue(), file_name="hasil_tiktok.xlsx")
            if res: st.dataframe(pd.DataFrame(res))
            if fail: st.error("Beberapa URL gagal, cek file download."); st.dataframe(pd.DataFrame(fail))
