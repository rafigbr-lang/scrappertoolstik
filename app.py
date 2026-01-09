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
st.set_page_config(page_title="TikTok Scalper Pro V2", page_icon="📊", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILS ---
def clean_money(value):
    if pd.isna(value): return 0
    cleaned = re.sub(r'[^\d]', '', str(value))
    return int(cleaned) if cleaned else 0

def extract_video_id(url):
    if pd.isna(url) or not isinstance(url, str): return None
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None

# --- CORE FUNCTIONS ---
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if not info: return None
        author = info.get("author", {})
        stats = info.get("stats", {})
        return {
            "video_url": url,
            "video_id": str(info.get("id")),
            "unique_id": author.get("uniqueId"), 
            "nickname": author.get("nickname"),
            "play_count": stats.get("playCount", 0),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except: return None

async def run_scraper(urls, token):
    results = []
    progress_bar = st.progress(0)
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[token], num_sessions=1, sleep_after=3, browser="chromium")
        for idx, url in enumerate(urls):
            data = await get_video_info(url, api)
            if data: results.append(data)
            progress_bar.progress((idx + 1) / len(urls))
            await asyncio.sleep(1)
    return results

# --- UI TABS ---
tab1, tab2 = st.tabs(["🔍 Step 1: Scraper", "🔗 Step 2: GMV Matcher"])

with tab1:
    st.header("TikTok Video Scraper")
    token = st.text_input("MS Token", type="password", key="token_tab1")
    uploaded_urls = st.file_uploader("Upload Excel berisi 'video_url'", type=["xlsx"], key="urls_tab1")
    
    if uploaded_urls and st.button("Start Scraping"):
        df_urls = pd.read_excel(uploaded_urls)
        urls = df_urls['video_url'].dropna().tolist()
        data_scraped = asyncio.run(run_scraper(urls, token))
        if data_scraped:
            df_res = pd.DataFrame(data_scraped)
            st.dataframe(df_res)
            # Simpan ke session state agar bisa dipakai di tab 2 tanpa upload ulang
            st.session_state['scraped_data'] = df_res
            st.success("Scraping Selesai! Lanjut ke Tab 2.")

with tab2:
    st.header("Smart GMV Matcher")
    st.write("Cocokkan hasil scraping dengan data GMV secara akurat.")
    
    col_a, col_b = st.columns(2)
    with col_a:
        # Bisa ambil dari tab 1 atau upload file baru
        scraped_file = st.file_uploader("Upload Hasil Scraping (jika tidak dari Step 1)", type=["xlsx"])
        if 'scraped_data' in st.session_state and not scraped_file:
            df_base = st.session_state['scraped_data']
            st.info("Menggunakan data dari Step 1")
        elif scraped_file:
            df_base = pd.read_excel(scraped_file)
        else:
            df_base = None

    with col_b:
        gmv_files = st.file_uploader("Upload File GMV (Bisa banyak)", type=["xlsx"], accept_multiple_files=True)

    if df_base is not None and gmv_files:
        if st.button("🔗 Run Precise Matching"):
            # 1. Gabung semua file GMV & Bersihkan
            df_gmv_all = pd.concat([pd.read_excel(f) for f in gmv_files], ignore_index=True)
            
            # Cari kolom GMV murni (Bukan Refunded)
            gmv_col = next((c for c in df_gmv_all.columns if c.strip() == 'GMV'), None)
            nickname_col = next((c for c in df_gmv_all.columns if 'nickname' in c.lower()), None)
            link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)

            if gmv_col:
                # Bersihkan data GMV
                df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(clean_money)
                
                # --- LOGIKA ANTI GHOSTING/DUPLIKAT ---
                # Menggunakan map dictionary (satu kunci satu nilai)
                # Ambil baris pertama jika ada duplikat nama creator di file GMV
                
                # A. Map Video ID
                if link_col:
                    df_gmv_all['v_id'] = df_gmv_all[link_col].apply(extract_video_id)
                    video_map = df_gmv_all.dropna(subset=['v_id']).drop_duplicates('v_id')
                    video_dict = dict(zip(video_map['v_id'], video_map[gmv_col]))
                    df_base['gmv_per_video'] = df_base['video_id'].map(video_dict).fillna(0)

                # B. Map Nickname
                if nickname_col:
                    # Ambil baris unik pertama untuk tiap nickname
                    user_map = df_gmv_all.dropna(subset=[nickname_col]).drop_duplicates(nickname_col)
                    user_dict = dict(zip(user_map[nickname_col], user_map[gmv_col]))
                    df_base['gmv_total_creator'] = df_base['nickname'].map(user_dict).fillna(0)
                
                st.subheader("Final Result")
                st.dataframe(df_base)
                
                # Download
                out = io.BytesIO()
                df_base.to_excel(out, index=False)
                st.download_button("📥 Download Final Report", out.getvalue(), "final_clean_report.xlsx")
            else:
                st.error("Kolom 'GMV' (tepat 3 huruf) tidak ditemukan di file GMV!")
