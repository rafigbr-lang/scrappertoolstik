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

# --- STABLE UTILITY FUNCTIONS ---
def clean_gmv_data(df):
    """Membersihkan data GMV dari simbol dan teks agar bisa dihitung"""
    # 1. Hapus kolom 'Refunded'
    df = df[[c for c in df.columns if 'refunded' not in c.lower()]]
    
    # 2. Filter status Refunded
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        df = df[df[status_col].astype(str).str.lower() != 'refunded']
    
    # 3. Konversi Kolom GMV ke Angka
    gmv_col = next((c for c in df.columns if 'gmv' in c.lower() and 'refund' not in c.lower()), None)
    if gmv_col:
        # Hapus simbol Rp, titik, atau koma agar menjadi angka murni
        df[gmv_col] = df[gmv_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df[gmv_col] = pd.to_numeric(df[gmv_col], errors='coerce').fillna(0)
        df = df[df[gmv_col] >= 0]
    
    return df, gmv_col

async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        author = info.get("author", {})
        stats = info.get("stats", {})
        return {
            "video_url": url,
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "play_count": int(stats.get("playCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except:
        return {"video_url": url, "error": "Failed"}

# --- UI STREAMLIT ---
st.title("🚀 TikTok Scalper + Multi-Match GMV")

# Inisialisasi session state agar data tidak hilang saat pindah tab
if 'scraped_df' not in st.session_state:
    st.session_state['scraped_df'] = None

with st.sidebar:
    st.header("⚙️ Settings")
    token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu...")

# Membuat Tab
tab1, tab2 = st.tabs(["🔍 Step 1: Scrape Data", "🔗 Step 2: Match & Integrate"])

with tab1:
    uploaded_main = st.file_uploader("Upload Excel Target (video_url)", type=["xlsx"], key="main_up")
    if uploaded_main:
        df_input = pd.read_excel(uploaded_main)
        if "video_url" in df_input.columns:
            urls = df_input["video_url"].dropna().tolist()
            st.info(f"📍 {len(urls)} URL siap diproses.")
            
            if st.button("🚀 Start Scraping"):
                results = []
                pbar = st.progress(0)
                status = st.empty()
                
                async def run_it():
                    async with TikTokApi() as api:
                        await api.create_sessions(ms_tokens=[token], num_sessions=1, sleep_after=2)
                        for i, url in enumerate(urls):
                            status.text(f"Processing {i+1}/{len(urls)}")
                            res = await get_video_info(url, api)
                            results.append(res)
                            pbar.progress((i + 1) / len(urls))
                        return results
                
                data = asyncio.run(run_it())
                st.session_state['scraped_df'] = pd.DataFrame(data)
                st.success("✅ Scraping Selesai!")
                st.dataframe(st.session_state['scraped_df'])
        else:
            st.error("Kolom 'video_url' tidak ditemukan.")

with tab2:
    st.subheader("Gabungkan dengan Data GMV")
    uploaded_gmv_list = st.file_uploader("Upload File GMV (Bisa banyak file)", type=["xlsx"], accept_multiple_files=True, key="gmv_up")

    if uploaded_gmv_list and st.session_state['scraped_df'] is not None:
        if st.button("🔗 Integrate & Sum GMV"):
            all_dfs = []
            for f in uploaded_gmv_list:
                temp_df, g_col = clean_gmv_data(pd.read_excel(f))
                all_dfs.append(temp_df)
            
            # Gabung semua file GMV
            df_gmv_all = pd.concat(all_dfs, ignore_index=True)
            
            # Cari kolom creator
            c_col = next((c for c in df_gmv_all.columns if 'creator name' in c.lower()), None)
            g_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower()), None)

            if c_col and g_col:
                # Grouping by Creator agar GMV-nya dijumlahkan (SUM)
                df_gmv_summed = df_gmv_all.groupby(c_col)[g_col].sum().reset_index()
                
                # Matching
                df_scrape = st.session_state['scraped_df']
                df_scrape['unique_id'] = df_scrape['unique_id'].astype(str).str.strip()
                df_gmv_summed[c_col] = df_gmv_summed[c_col].astype(str).str.strip()

                df_final = pd.merge(df_scrape, df_gmv_summed, left_on='unique_id', right_on=c_col, how='left')
                
                st.success("🔥 Data Berhasil Diintegrasikan!")
                st.dataframe(df_final)

                # Download
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False)
                st.download_button("📥 Download Hasil Akhir", output.getvalue(), file_name="final_report.xlsx")
            else:
                st.error("Gagal menemukan kolom 'creator name' atau 'GMV'.")
    elif st.session_state['scraped_df'] is None:
        st.warning("Selesaikan Step 1 dulu ya.")
