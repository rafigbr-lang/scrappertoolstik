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
st.set_page_config(page_title="TikTok Scalper Pro + GMV Matcher", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        return int(float(str(value).replace('Rp', '').replace('.', '').replace(',', '').strip()))
    except:
        return 0

def extract_video_id(url):
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
        if not info: return {"video_url": url, "error": "No data returned"}

        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})

        return {
            "video_url": url,
            "create_time": datetime.fromtimestamp(int(info.get("createTime", 0))).strftime("%Y-%m-%d %H:%M:%S") if info.get("createTime") else "N/A",
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

async def run_scraper(video_urls, ms_token):
    results, failed = [], []
    progress_bar = st.progress(0)
    status_text = st.empty()
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")
        for idx, url in enumerate(video_urls):
            status_text.write(f"⏳ Processing {idx+1}/{len(video_urls)}: {url}")
            data = await get_video_info(url, api)
            if "error" in data: failed.append(data)
            else: results.append(data)
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(1)
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Pro + GMV Matcher")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")

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
        
        if st.button("🚀 Run Scraping & Match GMV"):
            results, failed = asyncio.run(run_scraper(urls, token))
            
            if results:
                df_scraped = pd.DataFrame(results)
                
                if uploaded_gmv_list:
                    # Gabungkan semua file GMV
                    combined_gmv_list = [pd.read_excel(f) for f in uploaded_gmv_list]
                    df_gmv_all = pd.concat(combined_gmv_list, ignore_index=True)

                    # Tentukan kolom GMV dan abaikan Refunded GMV
                    # Kita cari kolom yang namanya TEPAT 'GMV' (bukan Refunded GMV)
                    gmv_col = None
                    for c in df_gmv_all.columns:
                        if c.strip().lower() == 'gmv': # Mencari kolom "GMV" saja
                            gmv_col = c
                            break
                    
                    # Jika tidak ketemu yang tepat "GMV", cari yang mengandung kata gmv tapi bukan refunded
                    if not gmv_col:
                        gmv_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower() and 'refunded' not in c.lower()), None)

                    link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                    creator_col = next((c for c in df_gmv_all.columns if 'creator name' in c.lower() or 'nickname' in c.lower()), None)

                    if gmv_col:
                        # 1. Matching Video ID
                        if link_col:
                            df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                            # Ambil nilai GMV apa adanya
                            df_gmv_video = df_gmv_all[['v_id_match', gmv_col]].rename(columns={gmv_col: 'gmv_video'})
                            df_scraped = pd.merge(df_scraped, df_gmv_video, left_on='video_id', right_on='v_id_match', how='left').drop(columns=['v_id_match'])

                        # 2. Matching Creator Name
                        if creator_col:
                            df_gmv_creator = df_gmv_all[[creator_col, gmv_col]].rename(columns={gmv_col: 'gmv_creator'})
                            # Jika ingin mencocokkan dengan unique_id atau nickname
                            df_scraped = pd.merge(df_scraped, df_gmv_creator, left_on='unique_id', right_on=creator_col, how='left').drop(columns=[creator_col])

                    # Atur urutan kolom
                    cols = df_scraped.columns.tolist()
                    if 'author_name' in cols:
                        target_idx = cols.index('author_name') + 1
                        for col_name in ['gmv_video', 'gmv_creator']:
                            if col_name in cols:
                                cols.insert(target_idx, cols.pop(cols.index(col_name)))
                    df_final = df_scraped[cols]
                else:
                    df_final = df_scraped

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name="Report")
                    if failed: pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Failed")
                
                st.success("✅ Selesai! Menggunakan nilai GMV murni (Refunded GMV diabaikan).")
                st.download_button("📥 Download Integrated Report", output.getvalue(), file_name="tiktok_final_report.xlsx")
                st.dataframe(df_final)
