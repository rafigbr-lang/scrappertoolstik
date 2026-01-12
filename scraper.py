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

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📊", layout="wide")

@st.cache_resource
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    return True

setup_browser()

# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        return int(value)
    except:
        return 0

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
            return {"video_url": url, "error": "No data returned from TikTok"}

        # Extraction Logic
        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})

        # Date Formatting
        raw_time = info.get("createTime", 0)
        try:
            formatted_time = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = "N/A"

        # Mapping 21 Kolom yang diminta
        return {
            "video_url": url,
            "create_time": formatted_time,
            "video_id": info.get("id") or video_data.get("id"),
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
            await asyncio.sleep(2) 
            
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Dashboard")

with st.sidebar:
    st.header("Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")
    st.info("Input file Excel harus memiliki kolom 'video_url'")

uploaded_file = st.file_uploader("Upload Input Excel", type=["xlsx"])

if uploaded_file:
    df_in = pd.read_excel(uploaded_file)
    if "video_url" in df_in.columns:
        urls = df_in["video_url"].dropna().tolist()
        st.success(f"Ready to scrape {len(urls)} videos")
        
        if st.button("Start Scraping"):
            res, fail = asyncio.run(run_scraper(urls, token))
            
            # Create Excel output
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if res: pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Success")
                if fail: pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Failed")
            
            st.divider()
            st.download_button("📥 Download Scraped Data", output.getvalue(), file_name="tiktok_full_results.xlsx")
            
            if res:
                st.subheader("Results Preview")
                st.dataframe(pd.DataFrame(res))
    else:
        st.error("Column 'video_url' not found!")
