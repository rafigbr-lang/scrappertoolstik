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
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📈", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        # Membersihkan format Rp, titik, dan koma agar menjadi angka murni
        clean_val = str(value).replace('Rp', '').replace('.', '').replace(',', '').strip()
        return int(float(clean_val))
    except:
        return 0

def extract_video_id(url):
    if pd.isna(url) or not isinstance(url, str): return None
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
            "unique_id": author.get("uniqueId"), # Ini username TikTok
            "nickname": author.get("nickname"),
            "author_name": author.get("nickname"),
            "play_count": safe_int(stats.get("playCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "comment_count": safe_int(stats.get("commentCount")),
            "share_count": safe_int(stats.get("shareCount")),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=2, browser="chromium")
        for idx, url in enumerate(video_urls):
            status_text.text(f"🔎 Scraping {idx+1}/{len(video_urls)}...")
            data = await get_video_info(url, api)
            if "error" in data: failed.append(data)
            else: results.append(data)
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(1)
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Pro - GMV Matcher")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

col1, col2 = st.columns(2)
with col1:
    st.subheader("1. File Target (Excel)")
    uploaded_main = st.file_uploader("Upload file berisi video_url", type=["xlsx"], key="main")
with col2:
    st.subheader("2. File Data GMV")
    uploaded_gmv_list = st.file_uploader("Upload file GMV (bisa banyak)", type=["xlsx"], accept_multiple_files=True, key="gmv")

if uploaded_main:
    df_main = pd.read_excel(uploaded_main)
    if "video_url" in df_main.columns:
        urls = df_main["video_url"].dropna().tolist()
        
        if st.button("🚀 Start Scraping & Match"):
            res_list, fail_list = asyncio.run(run_scraper(urls, token))
            
            if res_list:
                df_res = pd.DataFrame(res_list)
                
                # --- PROSES MATCHING GMV ---
                if uploaded_gmv_list:
                    # Gabung semua file GMV jadi satu referensi
                    df_gmv_all = pd.concat([pd.read_excel(f) for f in uploaded_gmv_list], ignore_index=True)
                    
                    # Identifikasi kolom secara dinamis
                    gmv_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower()), None)
                    link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                    creator_col = next((c for c in df_gmv_all.columns if 'creator name' in c.lower()), None)
                    
                    if gmv_col:
                        # Bersihkan angka GMV
                        df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(safe_int)
                        
                        # A. Match via Video ID (Link)
                        if link_col:
                            df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                            v_map = df_gmv_all.dropna(subset=['v_id_match']).set_index('v_id_match')[gmv_col].to_dict()
                            df_res['gmv_from_video'] = df_res['video_id'].map(v_map).fillna(0)
                        
                        # B. Match via Creator Name (Unique ID)
                        if creator_col:
                            # Ambil GMV tertinggi atau total per creator dari file referensi
                            c_map = df_gmv_all.dropna(subset=[creator_col]).groupby(creator_col)[gmv_col].sum().to_dict()
                            df_res['gmv_from_creator'] = df_res['unique_id'].map(c_map).fillna(0)

                # Tampilkan hasil
                st.success("✅ Selesai!")
                st.subheader("📊 Hasil Scraping & Matching")
                st.dataframe(df_res)
                
                # Export ke Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_res.to_excel(writer, index=False, sheet_name="Data_Detail")
                    if fail_list:
                        pd.DataFrame(fail_list).to_excel(writer, index=False, sheet_name="Gagal")
                
                st.download_button("📥 Download Integrated Report", output.getvalue(), file_name="tiktok_match_report.xlsx")
            else:
                st.error("Gagal mendapatkan data. Periksa token atau link.")
