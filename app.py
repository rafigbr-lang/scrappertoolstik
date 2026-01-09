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

# --- AUTO INSTALL PLAYWRIGHT ---
# Fungsi ini memastikan browser chromium terinstall saat dijalankan di Streamlit Cloud
def install_playwright():
    try:
        import playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    
    # Perintah untuk download browser chromium
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])

# Jalankan instalasi saat aplikasi pertama kali dibuka
if 'playwright_installed' not in st.session_state:
    with st.spinner("Sedang menyiapkan browser untuk scraping (ini hanya sekali)..."):
        install_playwright()
        st.session_state['playwright_installed'] = True

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)

st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📈", layout="wide")

# Token default (Bisa diedit lewat sidebar di web)
DEFAULT_MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info:
            raise ValueError("Video tidak ditemukan atau private")

        return {
            "video_url": url,
            "create_time": datetime.fromtimestamp(info.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
            "video_id": info.get("video", {}).get("id"),
            "nickname": info.get("author", {}).get("nickname"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "share_count": int(info.get("stats", {}).get("shareCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Scraper Engine ---------
async def run_scraper(video_urls, ms_token):
    results = []
    failed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser="chromium" 
        )

        for idx, url in enumerate(video_urls):
            status_text.text(f"🔎 Memproses {idx+1}/{len(video_urls)}: {url}")
            data = await get_video_info(url, api)
            
            if "error" in data:
                failed.append(data)
            else:
                results.append(data)
            
            progress_bar.progress((idx + 1) / len(video_urls))
            
    return results, failed

# --------- UI LAYOUT ---------
st.title("🚀 TikTok Scalper Dashboard")
st.info("Gunakan aplikasi ini untuk mengambil data statistik TikTok via file Excel.")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    token = st.text_input("MS Token", value=DEFAULT_MS_TOKEN, type="password")
    st.markdown("---")
    st.write("Pastikan file Excel memiliki kolom: `video_url`")

uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan di file tersebut!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"📂 Berhasil memuat {len(urls)} URL.")

        if st.button("🚀 Mulai Ambil Data"):
            # Menjalankan loop async
            results, failed = asyncio.run(run_scraper(urls, token))

            st.divider()
            st.subheader("✅ Hasil Scraping")

            # Download Button Logic
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if results:
                    pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Berhasil")
                if failed:
                    pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Gagal")
            
            st.download_button(
                label="📥 Download Hasil Excel",
                data=output.getvalue(),
                file_name=f"tiktok_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            # Tampilkan Preview
            if results:
                st.dataframe(pd.DataFrame(results))
            if failed:
                st.error(f"Gagal memproses {len(failed)} video.")
                with st.expander("Lihat Detail Error"):
                    st.table(pd.DataFrame(failed))
