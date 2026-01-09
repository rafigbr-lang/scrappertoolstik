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
st.set_page_config(page_title="TikTok Scalper Pro + Multi GMV", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        return int(float(value))
    except:
        return 0

def extract_video_id(url):
    """Mengekstrak ID angka dari link TikTok (setelah /video/)"""
    if pd.isna(url) or not isinstance(url, str):
        return None
    match = re.search(r'/video/(\d+)', url)
    return match.group(1) if match else None

def get_hashtags(text_extra):
    if not text_extra: return ""
    tags = [h.get("hashtagName") for h in text_extra if h.get("hashtagName")]
    return ", ".join(tags)

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        
        if not info:
            return {"video_url": url, "error": "No data returned"}

        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})

        raw_time = info.get("createTime", 0)
        try:
            formatted_time = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = "N/A"

        return {
            "video_url": url,
            "create_time": formatted_time,
            "video_id": str(info.get("id") or video_data.get("id")),
            "author_id": author.get("id"),
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "music_title": music.get("title"),
            "is_copyrighted": music.get("isCopyrighted"),
            "play_url": video_data.get("playAddr"),
            "author_name": music.get("authorName"),
            "hashtags": get_hashtags(info.get("textExtra")),
            "follower_count": safe_int(author_stats.get("followerCount")),
            "heart_count": safe_int(author_stats.get("heart")),
            "video_count": safe_int(author_stats.get("videoCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "comment_count": safe_int(stats.get("commentCount")),
            "play_count": safe_int(stats.get("playCount")),
            "collect_count": safe_int(stats_v2.get("collectCount") or stats.get("collectCount")),
            "share_count": safe_int(stats.get("shareCount")),
            "repost_count": safe_int(stats_v2.get("repostCount") or stats.get("repostCount")),
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
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")

        for idx, url in enumerate(video_urls):
            status_text.write(f"⏳ Processing {idx+1}/{len(video_urls)}: {url}")
            data = await get_video_info(url, api)
            
            if "error" in data:
                failed.append(data)
            else:
                results.append(data)
            
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(1)
            
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Pro + Multi-GMV Integrator")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. File Input Scraper")
    uploaded_main = st.file_uploader("Upload Excel (video_url)", type=["xlsx"], key="main")

with col2:
    st.subheader("2. File Data GMV (Bisa Banyak)")
    uploaded_gmv_list = st.file_uploader("Upload satu atau banyak file GMV", type=["xlsx"], accept_multiple_files=True, key="gmv_multi")

if uploaded_main:
    df_main_input = pd.read_excel(uploaded_main)
    
    if "video_url" in df_main_input.columns:
        urls = df_main_input["video_url"].dropna().tolist()
        
        if st.button("🚀 Run Scraping & Merge All GMV"):
            # 1. Scraping
            results, failed = asyncio.run(run_scraper(urls, token))
            
            if results:
                df_scraped = pd.DataFrame(results)
                
                # 2. Multi-GMV Integration
                if uploaded_gmv_list:
                    all_gmv_dfs = []
                    for uploaded_file in uploaded_gmv_list:
                        temp_df = pd.read_excel(uploaded_file)
                        all_gmv_dfs.append(temp_df)
                    
                    # Gabungkan semua file GMV jadi satu
                    df_gmv_combined = pd.concat(all_gmv_dfs, ignore_index=True)
                    
                    # Deteksi kolom
                    link_col = next((c for c in df_gmv_combined.columns if 'video link' in c.lower()), None)
                    gmv_col = next((c for c in df_gmv_combined.columns if 'gmv' in c.lower()), None)
                    
                    if link_col and gmv_col:
                        # Ekstrak ID
                        df_gmv_combined['video_id_extracted'] = df_gmv_combined[link_col].apply(extract_video_id)
                        
                        # Hapus duplikat ID jika ada video yang muncul di dua file berbeda (ambil data terbaru/teratas)
                        df_gmv_combined = df_gmv_combined.drop_duplicates(subset=['video_id_extracted'], keep='first')
                        
                        df_scraped['video_id'] = df_scraped['video_id'].astype(str)
                        df_gmv_combined['video_id_extracted'] = df_gmv_combined['video_id_extracted'].astype(str)
                        
                        # Merge
                        df_merge = pd.merge(
                            df_scraped, 
                            df_gmv_combined[['video_id_extracted', gmv_col]], 
                            left_on='video_id', 
                            right_on='video_id_extracted', 
                            how='left'
                        ).drop(columns=['video_id_extracted'])
                        
                        # Atur posisi kolom GMV setelah author_name
                        cols = df_merge.columns.tolist()
                        if gmv_col in cols:
                            idx = cols.index('author_name') + 1
                            cols.insert(idx, cols.pop(cols.index(gmv_col)))
                            df_final = df_merge[cols]
                        else:
                            df_final = df_merge
                    else:
                        st.warning("Kolom 'Video link' atau 'GMV' tidak ditemukan di file-file yang diupload.")
                        df_final = df_scraped
                else:
                    df_final = df_scraped
                    st.warning("Tidak ada file GMV yang diupload.")

                # 3. Output
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name="Integrated_Report")
                    if failed: pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Failed")
                
                st.success(f"✅ Selesai! Menggabungkan data dari {len(uploaded_gmv_list)} file GMV.")
                st.download_button("📥 Download Final Report", output.getvalue(), file_name="tiktok_multi_gmv_report.xlsx")
                st.dataframe(df_final)
