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
import re

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Pro - Fix GMV Ghosting", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None or pd.isna(value): return 0
        return int(float(str(value).replace('Rp', '').replace('.', '').replace(',', '').strip()))
    except:
        return 0

def extract_video_id(url):
    if pd.isna(url) or not isinstance(url, str):
        return None
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if not info: return {"video_url": url, "error": "No data returned"}

        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        video_data = info.get("video", {})

        return {
            "video_url": url,
            "video_id": str(info.get("id") or video_data.get("id")),
            "unique_id": author.get("uniqueId"), # Username (Penting untuk matching)
            "nickname": author.get("nickname"),
            "author_name": info.get("music", {}).get("authorName"),
            "follower_count": safe_int(author_stats.get("followerCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "play_count": safe_int(stats.get("playCount")),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")
        for idx, url in enumerate(video_urls):
            data = await get_video_info(url, api)
            if "error" in data: failed.append(data)
            else: results.append(data)
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(1)
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Pro (Anti-Wrong Match)")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. File Target Scraper")
    uploaded_main = st.file_uploader("Upload Excel (video_url)", type=["xlsx"])

with col2:
    st.subheader("2. File Data GMV")
    uploaded_gmv_list = st.file_uploader("Upload file GMV", type=["xlsx"], accept_multiple_files=True)

if uploaded_main:
    df_main_input = pd.read_excel(uploaded_main)
    if "video_url" in df_main_input.columns:
        urls = df_main_input["video_url"].dropna().tolist()
        
        if st.button("🚀 Run Scraping & Clean Match"):
            results, failed = asyncio.run(run_scraper(urls, token))
            
            if results:
                df_scraped = pd.DataFrame(results)
                
                if uploaded_gmv_list:
                    # Gabungkan semua file GMV
                    combined_gmv_list = [pd.read_excel(f) for f in uploaded_gmv_list]
                    df_gmv_all = pd.concat(combined_gmv_list, ignore_index=True)

                    # --- LOGIKA MATCHING YANG DIPERKETAT ---
                    # 1. Ambil kolom GMV (Bukan Refunded)
                    gmv_col = next((c for c in df_gmv_all.columns if c.strip().lower() == 'gmv'), None)
                    link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                    creator_col = next((c for c in df_gmv_all.columns if 'creator nickname' in c.lower() or 'nickname' in c.lower()), None)

                    if gmv_col:
                        # Bersihkan format mata uang di file GMV
                        df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(lambda x: safe_int(x))

                        # A. Match by Video Link (Prioritas Utama karena ID Video Unik)
                        if link_col:
                            df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                            # Agregasi agar tidak duplikat: 1 Video ID = Total GMV-nya
                            video_map = df_gmv_all.dropna(subset=['v_id_match']).groupby('v_id_match')[gmv_col].sum()
                            df_scraped['gmv_video'] = df_scraped['video_id'].map(video_map).fillna(0)

                        # B. Match by Creator Nickname (Hanya jika gmv_video masih 0)
                        if creator_col:
                            # Agregasi agar tidak duplikat: 1 Nickname = Total GMV-nya
                            creator_map = df_gmv_all.dropna(subset=[creator_col]).groupby(creator_col)[gmv_col].sum()
                            df_scraped['gmv_creator'] = df_scraped['nickname'].map(creator_map).fillna(0)
                    
                    df_final = df_scraped
                else:
                    df_final = df_scraped

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name="Report")
                
                st.success("✅ Selesai! Data dicocokkan secara ketat (Fillna 0 jika tidak ada).")
                st.download_button("📥 Download Report", output.getvalue(), file_name="tiktok_final_fix.xlsx")
                st.dataframe(df_final)
