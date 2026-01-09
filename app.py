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
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="💰", layout="wide")

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
    """Pembersihan data GMV: Hapus kolom/baris Refunded"""
    # 1. Buang kolom yang mengandung kata 'Refunded' secara spesifik
    cols_to_keep = [c for c in df.columns if 'refunded' not in c.lower() or 'gmv' in c.lower() and 'refunded gmv' not in c.lower()]
    df = df[cols_to_keep]
    
    # 2. Buang baris jika ada status 'Refunded'
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        df = df[df[status_col].astype(str).str.lower() != 'refunded']
    
    # 3. Pastikan GMV tidak ada yang negatif (biasanya kompensasi refund)
    gmv_col = next((c for c in df.columns if 'gmv' in c.lower() and 'refund' not in c.lower()), None)
    if gmv_col:
        df = df[df[gmv_col] >= 0]
        
    return df, gmv_col, status_col

async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if not info: return {"video_url": url, "error": "No data"}
        author = info.get("author", {})
        stats = info.get("stats", {})
        return {
            "video_url": url,
            "video_id": str(info.get("id") or info.get("video", {}).get("id")),
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "play_count": int(stats.get("playCount", 0)),
            "like_count": int(stats.get("diggCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --- UI STREAMLIT (Satu Tampilan Utama) ---
st.title("🚀 TikTok Scalper Pro + Multi-Match GMV")
st.divider()

# Bagian Sidebar untuk Token
with st.sidebar:
    st.header("⚙️ Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu...")
    st.info("Sistem akan otomatis menghapus kolom & baris bermuatan 'Refunded'.")

# 1. INPUT SECTION
st.subheader("📁 Step 1: Upload File")
col_a, col_b = st.columns(2)

with col_a:
    uploaded_main = st.file_uploader("Upload File Target (Excel berisi video_url)", type=["xlsx"])
with col_b:
    uploaded_gmv_list = st.file_uploader("Upload File GMV (Bisa pilih banyak file)", type=["xlsx"], accept_multiple_files=True)

st.divider()

# 2. PROCESSING SECTION
if uploaded_main:
    df_input = pd.read_excel(uploaded_main)
    if "video_url" in df_input.columns:
        urls = df_input["video_url"].dropna().tolist()
        st.write(f"📊 **Total URL ditemukan:** {len(urls)}")

        if st.button("🚀 Jalankan Proses Scraping & Matching", use_container_width=True):
            # --- START SCRAPING ---
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            async def start_scraping():
                async with TikTokApi() as api:
                    await api.create_sessions(ms_tokens=[token], num_sessions=1, sleep_after=2)
                    for idx, url in enumerate(urls):
                        status_text.text(f"🔍 Menarik data {idx+1}/{len(urls)}: {url}")
                        res = await get_video_info(url, api)
                        results.append(res)
                        progress_bar.progress((idx + 1) / len(urls))
                    return results

            scraped_data = asyncio.run(start_scraping())
            df_scrape = pd.DataFrame(scraped_data)
            
            # --- START GMV MATCHING (Jika ada file GMV) ---
            if uploaded_gmv_list:
                status_text.text("🔗 Menggabungkan data GMV dan membersihkan Refunded...")
                all_gmv_dfs = []
                for f in uploaded_gmv_list:
                    df_temp, g_col, s_col = clean_gmv_data(pd.read_excel(f))
                    all_gmv_dfs.append(df_temp)
                
                df_gmv_combined = pd.concat(all_gmv_dfs, ignore_index=True)
                
                # Identifikasi Kolom Kunci
                creator_col = next((c for c in df_gmv_combined.columns if 'creator name' in c.lower()), None)
                final_gmv_col = next((c for c in df_gmv_combined.columns if 'gmv' in c.lower()), None)

                if creator_col and final_gmv_col:
                    # Bersihkan spasi
                    df_scrape['unique_id'] = df_scrape['unique_id'].astype(str).str.strip()
                    df_gmv_combined[creator_col] = df_gmv_combined[creator_col].astype(str).str.strip()
                    
                    # Merge
                    df_final = pd.merge(
                        df_scrape, 
                        df_gmv_combined[[creator_col, final_gmv_col]], 
                        left_on='unique_id', 
                        right_on=creator_col, 
                        how='left'
                    ).drop(columns=[creator_col])
                else:
                    df_final = df_scrape
                    st.warning("⚠️ Kolom 'creator name' tidak ditemukan, hasil hanya data scraping saja.")
            else:
                df_final = df_scrape

            status_text.empty()
            progress_bar.empty()

            # --- 3. RESULT SECTION ---
            st.subheader("✅ Hasil Akhir")
            st.dataframe(df_final, use_container_width=True)
            
            # Download Button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Report Terintegrasi (.xlsx)",
                data=output.getvalue(),
                file_name=f"TikTok_GMV_Final_{datetime.now().strftime('%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.error("Kolom 'video_url' tidak ditemukan di file target.")
else:
    st.info("Menunggu upload file target untuk memulai.")
