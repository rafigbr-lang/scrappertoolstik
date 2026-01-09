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
st.set_page_config(page_title="TikTok Scalper Pro v2", page_icon="💰", layout="wide")

@st.cache_resource
def setup_browser():
    try:
        # Penting untuk Streamlit Cloud agar Playwright terinstall
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        return True
    except Exception as e:
        st.error(f"Gagal setup browser: {e}")
        return False

setup_browser()

# --- UTILITY FUNCTIONS ---
def clean_gmv_data(df):
    """Membersihkan data GMV dari refund dan memperbaiki tipe data angka"""
    df = df.copy()
    
    # 1. Hapus kolom yang mengandung kata 'Refunded'
    cols_to_keep = [c for c in df.columns if 'refunded' not in c.lower()]
    df = df[cols_to_keep]
    
    # 2. Cari kolom GMV dan Status
    gmv_col = next((c for c in df.columns if 'gmv' in c.lower() and 'refund' not in c.lower()), None)
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)

    # 3. Filter Status Refunded
    if status_col:
        df = df[df[status_col].astype(str).str.lower() != 'refunded']

    # 4. Perbaikan Tipe Data GMV (Mengatasi TypeError)
    if gmv_col:
        # Hapus simbol Rp, titik ribuan, dan ubah koma desimal ke titik
        df[gmv_col] = (
            df[gmv_col].astype(str)
            .str.replace(r'[RrpP. ]', '', regex=True)
            .str.replace(',', '.')
        )
        # Konversi ke numeric
        df[gmv_col] = pd.to_numeric(df[gmv_col], errors='coerce')
        # Hapus yang NaN dan pastikan >= 0
        df = df.dropna(subset=[gmv_col])
        df = df[df[gmv_col] >= 0]
        
    return df

async def get_video_info(url, api):
    """Helper untuk mengambil info video dengan proteksi error"""
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
            "comment_count": int(stats.get("commentCount", 0)),
            "share_count": int(stats.get("shareCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

async def run_it(urls, token, progress_bar, status_text):
    """Engine scraper dengan penanganan timeout"""
    results = []
    try:
        async with TikTokApi() as api:
            # Mengatur session dengan timeout internal
            await api.create_sessions(ms_tokens=[token], num_sessions=1, sleep_after=3)
            
            for idx, url in enumerate(urls):
                status_text.text(f"⏳ Mengambil data {idx+1}/{len(urls)}: {url}")
                res = await get_video_info(url, api)
                results.append(res)
                progress_bar.progress((idx + 1) / len(urls))
                await asyncio.sleep(1) # Jeda agar tidak terkena rate limit
    except Exception as e:
        st.error(f"Terjadi kesalahan pada koneksi TikTok: {e}")
    return results

# --- UI STREAMLIT ---
st.title("🚀 TikTok Scalper Pro + Smart GMV Matching")

with st.sidebar:
    st.header("⚙️ Settings")
    ms_token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")
    st.markdown("---")
    st.write("Pastikan kolom target di file GMV bernama **'creator name'**.")

tab1, tab2 = st.tabs(["🔍 1. Scrape TikTok", "🔗 2. Integrate GMV"])

with tab1:
    uploaded_main = st.file_uploader("Upload File Target (Excel)", type=["xlsx"])
    if uploaded_main:
        df_urls = pd.read_excel(uploaded_main)
        if "video_url" in df_urls.columns:
            urls_list = df_urls["video_url"].dropna().tolist()
            st.info(f"Siap memproses {len(urls_list)} URL.")
            
            if st.button("🚀 Jalankan Scraper"):
                prog = st.progress(0)
                stat = st.empty()
                
                # Jalankan asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                final_data = loop.run_until_complete(run_it(urls_list, ms_token, prog, stat))
                
                st.session_state['scraped_df'] = pd.DataFrame(final_data)
                st.success("Scraping Selesai!")
                st.dataframe(st.session_state['scraped_df'])
        else:
            st.error("Kolom 'video_url' tidak ditemukan!")

with tab2:
    st.subheader("Gabungkan Multi-File GMV")
    uploaded_gmv_files = st.file_uploader("Upload file-file GMV", type=["xlsx"], accept_multiple_files=True)
    
    if uploaded_gmv_files:
        if 'scraped_df' not in st.session_state:
            st.warning("Silahkan lakukan Scraping di Tab 1 terlebih dahulu.")
        else:
            if st.button("🔗 Proses Integrasi"):
                with st.spinner("Menggabungkan data..."):
                    all_gmv = []
                    for f in uploaded_gmv_files:
                        df_temp = pd.read_excel(f)
                        all_gmv.append(clean_gmv_data(df_temp))
                    
                    df_gmv_final = pd.concat(all_gmv, ignore_index=True)
                    
                    # Cari kolom kunci
                    creator_col = next((c for c in df_gmv_final.columns if 'creator name' in c.lower()), None)
                    gmv_val_col = next((c for c in df_gmv_final.columns if 'gmv' in c.lower()), None)

                    if creator_col and gmv_val_col:
                        # Membersihkan spasi
                        df_scraped = st.session_state['scraped_df']
                        df_scraped['unique_id'] = df_scraped['unique_id'].astype(str).str.strip()
                        df_gmv_final[creator_col] = df_gmv_final[creator_col].astype(str).str.strip()
                        
                        # Gabungkan
                        df_merged = pd.merge(
                            df_scraped, 
                            df_gmv_final[[creator_col, gmv_val_col]], 
                            left_on='unique_id', 
                            right_on=creator_col, 
                            how='left'
                        ).drop(columns=[creator_col])
                        
                        st.success("Integrasi Berhasil!")
                        st.dataframe(df_merged)
                        
                        # Tombol Download
                        out = io.BytesIO()
                        with pd.ExcelWriter(out, engine='openpyxl') as writer:
                            df_merged.to_excel(writer, index=False)
                        
                        st.download_button("📥 Download Excel Hasil Integrasi", out.getvalue(), file_name="final_report_integrated.xlsx")
                    else:
                        st.error("Kolom 'creator name' atau 'GMV' tidak ditemukan pada file yang diupload.")
