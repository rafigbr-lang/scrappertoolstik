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
st.set_page_config(page_title="TikTok Scalper Pro + GMV Integrator", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        return True
    except:
        return False

setup_browser()

# --- UTILITY FUNCTIONS ---
def clean_gmv_data(df):
    """Fungsi untuk membersihkan data GMV dari Refunded"""
    # 1. Hapus kolom yang mengandung kata 'Refunded' (Refunded GMV, dll)
    cols_to_keep = [c for c in df.columns if 'refunded' not in c.lower()]
    df = df[cols_to_keep]
    
    # 2. Hapus baris jika ada kolom 'Status' yang isinya 'Refunded'
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        df = df[df[status_col].astype(str).str.lower() != 'refunded']
    
    # 3. Cari kolom GMV utama untuk memastikan nilainya bersih
    gmv_col = next((c for c in df.columns if 'gmv' in c.lower() and 'refund' not in c.lower()), None)
    if gmv_col:
        # Jika ada GMV negatif (seringkali refund), kita buang atau nol kan
        df = df[df[gmv_col] >= 0]
        
    return df

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
            "unique_id": author.get("uniqueId"), # Username untuk matching
            "nickname": author.get("nickname"),
            "author_name_music": info.get("music", {}).get("authorName"),
            "play_count": int(stats.get("playCount", 0)),
            "like_count": int(stats.get("diggCount", 0)),
            "comment_count": int(stats.get("commentCount", 0)),
            "share_count": int(stats.get("shareCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --- UI STREAMLIT ---
st.title("🚀 TikTok Scalper + Smart GMV Integrator")
st.markdown("Scrape data TikTok dan gabungkan dengan data GMV dari banyak file sekaligus.")

with st.sidebar:
    st.header("⚙️ Configuration")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu...")
    st.info("Pastikan kolom di file GMV bernama 'creator name' agar matching berhasil.")

# Menggunakan Tabs agar UI bersih
tab_scrape, tab_match = st.tabs(["🔍 1. Scrape Data", "🔗 2. Match GMV"])

with tab_scrape:
    uploaded_main = st.file_uploader("Upload Excel Target (Harus ada kolom 'video_url')", type=["xlsx"])
    
    if uploaded_main:
        df_input = pd.read_excel(uploaded_main)
        if "video_url" in df_input.columns:
            urls = df_input["video_url"].dropna().tolist()
            st.success(f"Ditemukan {len(urls)} URL.")
            
            if st.button("🚀 Mulai Scraping"):
                results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                async def run_it():
                    async with TikTokApi() as api:
                        await api.create_sessions(ms_tokens=[token], num_sessions=1, sleep_after=2)
                        for idx, url in enumerate(urls):
                            status_text.text(f"Scraping {idx+1}/{len(urls)}: {url}")
                            res = await get_video_info(url, api)
                            results.append(res)
                            progress_bar.progress((idx + 1) / len(urls))
                        return results

                final_res = asyncio.run(run_it())
                st.session_state['scraped_df'] = pd.DataFrame(final_res)
                st.success("✅ Scraping selesai! Silahkan buka tab '2. Match GMV'.")
                st.dataframe(st.session_state['scraped_df'].head())
        else:
            st.error("Kolom 'video_url' tidak ditemukan di file ini.")

with tab_match:
    st.subheader("Integrasi Banyak File GMV")
    uploaded_gmv_list = st.file_uploader("Upload satu atau lebih file GMV (.xlsx)", type=["xlsx"], accept_multiple_files=True)

    if uploaded_gmv_list:
        if 'scraped_df' not in st.session_state:
            st.warning("⚠️ Harap lakukan scraping di Tab 1 terlebih dahulu.")
        else:
            if st.button("🔗 Gabungkan & Match Sekarang"):
                all_gmv_dfs = []
                
                for f in uploaded_gmv_list:
                    df_gmv = pd.read_excel(f)
                    # Bersihkan dari refunded
                    df_gmv = clean_gmv_data(df_gmv)
                    all_gmv_dfs.append(df_gmv)
                
                # Gabungkan semua file GMV jadi satu
                df_gmv_combined = pd.concat(all_gmv_dfs, ignore_index=True)
                
                # Proses Matching
                df_scrape = st.session_state['scraped_df']
                
                # Identifikasi kolom GMV (mencari kolom yang ada kata 'gmv')
                gmv_col = next((c for c in df_gmv_combined.columns if 'gmv' in c.lower()), None)
                creator_col = next((c for c in df_gmv_combined.columns if 'creator name' in c.lower()), None)

                if creator_col and gmv_col:
                    # Bersihkan spasi pada kolom kunci
                    df_scrape['unique_id'] = df_scrape['unique_id'].astype(str).str.strip()
                    df_gmv_combined[creator_col] = df_gmv_combined[creator_col].astype(str).str.strip()
                    
                    # Merge data
                    df_final = pd.merge(
                        df_scrape, 
                        df_gmv_combined[[creator_col, gmv_col]], 
                        left_on='unique_id', 
                        right_on=creator_col, 
                        how='left'
                    ).drop(columns=[creator_col])
                    
                    st.success("🎉 Berhasil Menggabungkan Data!")
                    st.dataframe(df_final)
                    
                    # Download
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_final.to_excel(writer, index=False)
                    
                    st.download_button(
                        "📥 Download Final Integrated Report",
                        output.getvalue(),
                        file_name=f"TikTok_GMV_Report_{datetime.now().strftime('%d%m%Y')}.xlsx"
                    )
                else:
                    st.error(f"Kolom 'creator name' atau 'GMV' tidak ditemukan di file yang diupload. Kolom tersedia: {list(df_gmv_combined.columns)}")
