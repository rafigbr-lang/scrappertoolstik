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
st.set_page_config(page_title="TikTok Scalper Pro + Recap", page_icon="📊", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        # Membersihkan format Rupiah atau simbol lainnya
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
        return {
            "video_url": url,
            "video_id": str(info.get("id") or info.get("video", {}).get("id")),
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
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
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=2, browser="chromium")
        for idx, url in enumerate(video_urls):
            data = await get_video_info(url, api)
            if "error" in data: failed.append(data)
            else: results.append(data)
            progress_bar.progress((idx + 1) / len(video_urls))
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper & Creator Recapitulation")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

col1, col2 = st.columns(2)
with col1:
    uploaded_main = st.file_uploader("1. Upload Target Scraping (Excel)", type=["xlsx"])
with col2:
    uploaded_gmv_list = st.file_uploader("2. Upload File GMV (Multiple)", type=["xlsx"], accept_multiple_files=True)

if uploaded_main:
    df_main = pd.read_excel(uploaded_main)
    if "video_url" in df_main.columns:
        urls = df_main["video_url"].dropna().tolist()
        
        if st.button("🚀 Process & Generate Recap"):
            results, failed = asyncio.run(run_scraper(urls, token))
            
            if results:
                df_res = pd.DataFrame(results)
                
                # --- INTEGRASI GMV ---
                if uploaded_gmv_list:
                    df_gmv_all = pd.concat([pd.read_excel(f) for f in uploaded_gmv_list], ignore_index=True)
                    # Mencari kolom GMV & Link
                    link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                    gmv_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower()), None)
                    
                    if link_col and gmv_col:
                        df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                        df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(safe_int)
                        
                        df_res = pd.merge(df_res, df_gmv_all[['v_id_match', gmv_col]].rename(columns={gmv_col: 'gmv'}), 
                                          left_on='video_id', right_on='v_id_match', how='left').drop(columns=['v_id_match'])
                        df_res['gmv'] = df_res['gmv'].fillna(0)

                # --- FITUR RECAP KREATOR ---
                # Menghitung jumlah video, total views, dan total GMV per username
                df_recap = df_res.groupby('unique_id').agg({
                    'video_url': 'count',
                    'play_count': 'sum',
                    'gmv': 'sum' if 'gmv' in df_res.columns else 'max' # max jika gmv tdk ada
                }).reset_index().rename(columns={'video_url': 'total_videos', 'play_count': 'total_views', 'gmv': 'total_gmv'})

                # --- UI OUTPUT & SORTING ---
                st.divider()
                st.subheader("📊 Analisis & Sorting")
                
                sort_option = st.selectbox("Urutkan Data Recap Berdasarkan:", 
                                            ["GMV Terbesar", "GMV Terkecil", "Views Tertinggi", "Jumlah Video Terbanyak"])
                
                if sort_option == "GMV Terbesar":
                    df_recap = df_recap.sort_values(by='total_gmv', ascending=False)
                elif sort_option == "GMV Terkecil":
                    df_recap = df_recap.sort_values(by='total_gmv', ascending=True)
                elif sort_option == "Views Tertinggi":
                    df_recap = df_recap.sort_values(by='total_views', ascending=False)
                elif sort_option == "Jumlah Video Terbanyak":
                    df_recap = df_recap.sort_values(by='total_videos', ascending=False)

                st.write("### Recap Per Kreator")
                st.dataframe(df_recap, use_container_width=True)

                st.write("### Data Detail Video")
                st.dataframe(df_res)

                # --- DOWNLOAD ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_recap.to_excel(writer, index=False, sheet_name="Recap_Kreator")
                    df_res.to_excel(writer, index=False, sheet_name="Detail_Video")
                
                st.download_button("📥 Download Integrated Report (Recap + Detail)", 
                                   output.getvalue(), file_name="tiktok_final_recap.xlsx")
