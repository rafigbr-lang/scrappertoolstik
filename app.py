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

# --- Konfigurasi Log & Halaman ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📈", layout="wide")

# --- Inisialisasi Browser (PENTING) ---
@st.cache_resource
def setup_browser():
    # Menjalankan instalasi browser playwright secara otomatis
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# Token Default
DEFAULT_MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        
        if not info:
            return {"video_url": url, "error": "Gagal mengambil data (IP diblokir/Token Expired)"}

        return {
            "video_url": url,
            "create_time": datetime.fromtimestamp(info.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
            "nickname": info.get("author", {}).get("nickname"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Scraper Engine ---------
async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    async with TikTokApi() as api:
        try:
            await api.create_sessions(
                ms_tokens=[ms_token],
                num_sessions=1,
                sleep_after=3,
                browser="chromium"
            )

            for idx, url in enumerate(video_urls):
                status_text.write(f"🔍 Memproses ({idx+1}/{len(video_urls)}): {url}")
                data = await get_video_info(url, api)
                
                if "error" in data:
                    failed.append(data)
                else:
                    results.append(data)
                
                progress_bar.progress((idx + 1) / len(video_urls))
                await asyncio.sleep(1) # Delay kecil
        except Exception as e:
            st.error(f"Koneksi Gagal: {e}")
            
    return results, failed

# --------- UI DASHBOARD ---------
st.title("🚀 TikTok Scalper Dashboard")

with st.sidebar:
    st.header("⚙️ Settings")
    token = st.text_input("MS Token", value=DEFAULT_MS_TOKEN, type="password")
    st.info("Pastikan file Excel memiliki kolom: `video_url`")

uploaded_file = st.file_uploader("Upload Excel Input (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file, engine='openpyxl')
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"📂 {len(urls)} URL siap diproses.")

        if st.button("Mulai Scraping Sekarang"):
            results, failed = asyncio.run(run_scraper(urls, token))

            # Hasil Export
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if results: pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Berhasil")
                if failed: pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Gagal")
            
            st.divider()
            st.download_button("📥 Download Hasil Scraping", output.getvalue(), 
                               file_name=f"hasil_scraping_{datetime.now().strftime('%d%m%y')}.xlsx", 
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
            if results: 
                st.subheader("Preview Data Berhasil")
                st.table(pd.DataFrame(results).head(10))
