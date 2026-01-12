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
st.set_page_config(page_title="TikTok Scalper Pro - Fix GMV Accuracy", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def clean_money_to_int(value):
    """Mengubah format Rp762.992 atau string lainnya menjadi angka murni 762992"""
    try:
        if value is None or pd.isna(value): return 0
        # Hapus Rp, titik, koma, dan spasi
        cleaned = re.sub(r'[^\d]', '', str(value))
        return int(cleaned) if cleaned else 0
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
        stats = info.get("stats", {})
        video_data = info.get("video", {})

        return {
            "video_url": url,
            "video_id": str(info.get("id") or video_data.get("id")),
            "unique_id": author.get("uniqueId"), 
            "nickname": author.get("nickname"),
            "author_name": info.get("music", {}).get("authorName"),
            "play_count": clean_money_to_int(stats.get("playCount")),
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
st.title("🚀 TikTok Scalper Pro (Accuracy Mode)")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password")
    st.warning("Mode ini akan mengambil nilai GMV murni tanpa menjumlahkannya jika ada duplikat.")

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
        
        if st.button("🚀 Run Scraping & Match Accurate GMV"):
            results, failed = asyncio.run(run_scraper(urls, token))
            
            if results:
                df_scraped = pd.DataFrame(results)
                
                if uploaded_gmv_list:
                    # 1. Gabungkan semua file GMV
                    combined_gmv_list = [pd.read_excel(f) for f in uploaded_gmv_list]
                    df_gmv_raw = pd.concat(combined_gmv_list, ignore_index=True)

                    # 2. Identifikasi Kolom (Cari kolom GMV yang bukan 'Refunded GMV')
                    # Kita pakai pendekatan: ambil kolom yang namanya TEPAT 'GMV'
                    gmv_col = next((c for c in df_gmv_raw.columns if c.strip() == 'GMV'), None)
                    link_col = next((c for c in df_gmv_raw.columns if 'video link' in c.lower()), None)
                    nickname_col = next((c for c in df_gmv_raw.columns if 'nickname' in c.lower()), None)

                    if gmv_col:
                        # 3. Bersihkan angka GMV agar menjadi integer murni
                        df_gmv_raw[gmv_col] = df_gmv_raw[gmv_col].apply(clean_money_to_int)

                        # --- FIX: LOGIKA ANTI-DOUBLE ---
                        # Kita hapus duplikat di file GMV, ambil baris pertama yang muncul untuk setiap creator/video
                        # Ini mencegah penjumlahan yang bikin angka jadi 4jt padahal aslinya 700rb
                        
                        # A. Match by Video ID (Sangat Akurat)
                        if link_col:
                            df_gmv_raw['v_id_match'] = df_gmv_raw[link_col].apply(extract_video_id)
                            # Buat map unik: satu video id -> satu nilai gmv
                            video_map = df_gmv_raw.dropna(subset=['v_id_match']).drop_duplicates('v_id_match')
                            video_dict = dict(zip(video_map['v_id_match'], video_map[gmv_col]))
                            df_scraped['gmv_video'] = df_scraped['video_id'].map(video_dict).fillna(0)

                        # B. Match by Nickname (Hanya jika gmv_video masih 0)
                        if nickname_col:
                            # Buat map unik: satu nickname -> satu nilai gmv
                            creator_map = df_gmv_raw.dropna(subset=[nickname_col]).drop_duplicates(nickname_col)
                            creator_dict = dict(zip(creator_map[nickname_col], creator_map[gmv_col]))
                            
                            # Isi gmv_creator
                            df_scraped['gmv_creator'] = df_scraped['nickname'].map(creator_dict).fillna(0)

                    df_final = df_scraped
                else:
                    df_final = df_scraped

                # Export ke Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name="Report")
                
                st.success("✅ Selesai! Angka GMV diambil secara unik (Tidak dijumlahkan jika dobel).")
                st.download_button("📥 Download Accurate Report", output.getvalue(), file_name="tiktok_fixed_accuracy.xlsx")
                st.dataframe(df_final)
