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
        # Membersihkan format Rupiah, titik, koma
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
            status_text.text(f"🔎 Scaping {idx+1}/{len(video_urls)}...")
            data = await get_video_info(url, api)
            if "error" in data: failed.append(data)
            else: results.append(data)
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(1)
    return results, failed

# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper & Creator Recap")

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
        
        if st.button("🚀 Process Data"):
            res_list, fail_list = asyncio.run(run_scraper(urls, token))
            
            if res_list:
                df_res = pd.DataFrame(res_list)
                
                # --- INTEGRASI GMV (Video ID & Creator Name) ---
                df_res['gmv'] = 0
                if uploaded_gmv_list:
                    df_gmv_all = pd.concat([pd.read_excel(f) for f in uploaded_gmv_list], ignore_index=True)
                    
                    # Normalisasi GMV
                    gmv_col = next((c for c in df_gmv_all.columns if 'gmv' in c.lower()), None)
                    if gmv_col:
                        df_gmv_all[gmv_col] = df_gmv_all[gmv_col].apply(safe_int)
                        
                        # Match by Video Link
                        link_col = next((c for c in df_gmv_all.columns if 'video link' in c.lower()), None)
                        if link_col:
                            df_gmv_all['v_id_match'] = df_gmv_all[link_col].apply(extract_video_id)
                            # Create mapping dict
                            v_map = df_gmv_all.dropna(subset=['v_id_match']).set_index('v_id_match')[gmv_col].to_dict()
                            df_res['gmv'] = df_res['video_id'].map(v_map).fillna(0)
                        
                        # Match by Creator Name (Jika GMV video masih 0)
                        creator_col = next((c for c in df_gmv_all.columns if 'creator name' in c.lower()), None)
                        if creator_col:
                            c_map = df_gmv_all.dropna(subset=[creator_col]).groupby(creator_col)[gmv_col].sum().to_dict()
                            # Hanya update jika gmv video masih 0 (opsional, bisa juga dijumlah)
                            df_res['gmv_creator_total'] = df_res['unique_id'].map(c_map).fillna(0)

                # --- FIX RECAP LOGIC ---
                # Memastikan kolom ada sebelum groupby
                required_cols = ['unique_id', 'video_url', 'play_count', 'gmv']
                for col in required_cols:
                    if col not in df_res.columns: df_res[col] = 0 if col != 'unique_id' else "Unknown"

                df_recap = df_res.groupby('unique_id').agg({
                    'video_url': 'count',
                    'play_count': 'sum',
                    'gmv': 'sum'
                }).reset_index().rename(columns={
                    'video_url': 'total_videos', 
                    'play_count': 'total_views', 
                    'gmv': 'total_gmv'
                })

                # --- UI OUTPUT & SORTING ---
                st.divider()
                st.subheader("📊 Analisis & Sorting")
                
                sort_option = st.selectbox("Urutkan Data Recap:", 
                                            ["GMV Terbesar", "Views Tertinggi", "Paling Produktif (Video)"])
                
                sort_map = {
                    "GMV Terbesar": ('total_gmv', False),
                    "Views Tertinggi": ('total_views', False),
                    "Paling Produktif (Video)": ('total_videos', False)
                }
                
                col_sort, asc_sort = sort_map[sort_option]
                df_recap = df_recap.sort_values(by=col_sort, ascending=asc_sort)

                st.write("### Recap Per Kreator")
                st.dataframe(df_recap, use_container_width=True)

                st.write("### Detail Per Video")
                st.dataframe(df_res)

                # --- DOWNLOAD ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_recap.to_excel(writer, index=False, sheet_name="Recap_Kreator")
                    df_res.to_excel(writer, index=False, sheet_name="Detail_Video")
                    if fail_list: pd.DataFrame(fail_list).to_excel(writer, index=False, sheet_name="Gagal")
                
                st.download_button("📥 Download Hasil Akhir", output.getvalue(), file_name="tiktok_final_report.xlsx")
            else:
                st.error("❌ Tidak ada data yang berhasil di-scrape. Cek MS Token atau koneksi.")
    else:
        st.error("Kolom 'video_url' tidak ditemukan!")
