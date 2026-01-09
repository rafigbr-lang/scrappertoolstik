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
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "author_name": author.get("nickname"), # alias untuk matching
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
st.title("🚀 TikTok Scalper Pro")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

col1, col2 = st.columns(2)
with col1:
    uploaded_main = st.file_uploader("1. Upload Target (Excel)", type=["xlsx"])
with col2:
    uploaded_gmv_list = st.file_uploader("2. Upload GMV (Multiple)", type=["xlsx"], accept_multiple_files=True)

# Session state untuk menyimpan hasil agar tidak hilang saat klik tombol recap
if 'df_final_results' not in st.session_state:
    st.session_state.df_final_results = None
if 'failed_list' not in st.session_state:
    st.session_state.failed_list = None

if uploaded_main:
    df_main = pd.read_excel(uploaded_main)
    if "video_url" in df_main.columns:
        urls = df_main["video_url"].dropna().tolist()
        
        if st.button("🚀 Start Scraping"):
            res_list, fail_list = asyncio.run(run_scraper(urls, token))
            
            if res_list:
                df_res = pd.DataFrame(res_list)
                
                # --- INTEGRASI GMV (Dilakukan otomatis setelah scrape) ---
                if uploaded_gmv_list:
                    df_gmv_all = pd.concat([pd.read_excel(f) for f in uploaded_gmv_list], ignore_index=True)
                    gmv_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower()), None)
                    link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                    
                    if gmv_col and link_col:
                        df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(safe_int)
                        df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                        v_map = df_gmv_all.dropna(subset=['v_id_match']).set_index('v_id_match')[gmv_col].to_dict()
                        df_res['gmv'] = df_res['video_id'].map(v_map).fillna(0)
                        
                        # Atur posisi kolom GMV setelah author_name
                        cols = df_res.columns.tolist()
                        if 'gmv' in cols:
                            idx = cols.index('nickname') + 1 # geser ke setelah nickname/author_name
                            cols.insert(idx, cols.pop(cols.index('gmv')))
                            df_res = df_res[cols]

                st.session_state.df_final_results = df_res
                st.session_state.failed_list = fail_list
                st.success("✅ Scraping Selesai!")

        # --- TAMPILAN DATA AWAL (Detail Video) ---
        if st.session_state.df_final_results is not None:
            st.subheader("📄 Raw Scraping Results")
            st.dataframe(st.session_state.df_final_results)
            
            # Download Data Detail
            output_detail = io.BytesIO()
            with pd.ExcelWriter(output_detail, engine='openpyxl') as writer:
                st.session_state.df_final_results.to_excel(writer, index=False)
            st.download_button("📥 Download Detail Video", output_detail.getvalue(), file_name="tiktok_detail.xlsx")

            st.divider()

            # --- TOMBOL RECAP (OPSIONAL) ---
            st.subheader("📊 Creator Analysis")
            if st.button("📈 Generate Recap & Ranking"):
                df_res = st.session_state.df_final_results
                
                # Pastikan kolom gmv ada
                if 'gmv' not in df_res.columns: df_res['gmv'] = 0

                # Recap Logic
                df_recap = df_res.groupby('unique_id').agg({
                    'video_url': 'count',
                    'play_count': 'sum',
                    'gmv': 'sum'
                }).reset_index().rename(columns={
                    'video_url': 'total_videos', 
                    'play_count': 'total_views', 
                    'gmv': 'total_gmv'
                })

                # Sorting UI
                sort_option = st.selectbox("Urutkan Recap:", 
                                            ["GMV Terbesar", "Views Tertinggi", "Paling Produktif"])
                
                if sort_option == "GMV Terbesar":
                    df_recap = df_recap.sort_values('total_gmv', ascending=False)
                elif sort_option == "Views Tertinggi":
                    df_recap = df_recap.sort_values('total_views', ascending=False)
                else:
                    df_recap = df_recap.sort_values('total_videos', ascending=False)

                st.write("#### Recap Per Kreator")
                st.dataframe(df_recap, use_container_width=True)

                # Download Recap
                output_recap = io.BytesIO()
                with pd.ExcelWriter(output_recap, engine='openpyxl') as writer:
                    df_recap.to_excel(writer, index=False)
                st.download_button("📥 Download Recap Report", output_recap.getvalue(), file_name="tiktok_recap.xlsx")
