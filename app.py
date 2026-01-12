import streamlit as st
import pandas as pd
import asyncio
from TikTokApi import TikTokApi
import os
from datetime import datetime
import io
import subprocess

# --- 1. AUTO INSTALLER PLAYWRIGHT (WAJIB UNTUK STREAMLIT CLOUD) ---
def install_playwright():
    try:
        # Install browser chromium dan dependensi sistemnya
        subprocess.run(["playwright", "install", "chromium"], check=True)
        subprocess.run(["playwright", "install-deps"], check=True)
    except Exception as e:
        st.error(f"Gagal inisialisasi browser: {e}")

if 'playwright_installed' not in st.session_state:
    with st.spinner("Sedang menyiapkan mesin browser (hanya dilakukan sekali)..."):
        install_playwright()
        st.session_state['playwright_installed'] = True

# --- 2. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="TikTok Data Scalper", page_icon="📱", layout="wide")

# Masukkan ms_token terbaru Anda di sini
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --- 3. FUNGSI SCRAPER ---
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if not info or "author" not in info:
            return {"video_url": url, "error": "Gagal: Video Private/Sudah Dihapus atau Token Expired"}

        stats = info.get("stats", {})
        author_stats = info.get("authorStats", {})
        
        return {
            "video_url": url,
            "video_id": info.get("id"),
            "create_time": datetime.fromtimestamp(info.get("createTime", 0)).strftime("%Y-%m-%d %H:%M:%S"),
            "author": info.get("author", {}).get("uniqueId"),
            "nickname": info.get("author", {}).get("nickname"),
            "followers": int(author_stats.get("followerCount", 0)),
            "plays": int(stats.get("playCount", 0)),
            "likes": int(stats.get("diggCount", 0)),
            "comments": int(stats.get("commentCount", 0)),
            "shares": int(stats.get("shareCount", 0)),
            "saved": int(stats.get("collectCount", 0)),
            "hashtags": ", ".join([h["hashtagName"] for h in info.get("textExtra", []) if h.get("hashtagName")]),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": f"Error: {str(e)}"}

# --- 4. ANTARMUKA (UI) ---
st.title("📱 TikTok Data Scalper Pro")
st.markdown("Aplikasi untuk scraping data video TikTok dari daftar URL di Excel secara otomatis.")

# Sidebar untuk konfigurasi tambahan
with st.sidebar:
    st.header("Konfigurasi")
    delay_time = st.slider("Jeda antar video (detik)", 1.0, 10.0, 2.5)
    st.info("Gunakan jeda lebih lama jika sering gagal (biar tidak dianggap bot).")

uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    df_input = pd.read_excel(uploaded_file)
    
    if "video_url" not in df_input.columns:
        st.error("❌ Kolom 'video_url' tidak ditemukan!")
    else:
        urls = df_input["video_url"].dropna().tolist()
        st.success(f"✅ Terdeteksi {len(urls)} link video siap diproses.")
        
        if st.button("🚀 Mulai Ambil Data"):
            results = []
            failed = []
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            async def run_scraper():
                try:
                    async with TikTokApi() as api:
                        # Inisialisasi session
                        await api.create_sessions(ms_tokens=[MS_TOKEN], num_sessions=1, sleep_after=3)
                        
                        for idx, url in enumerate(urls):
                            status_text.text(f"Memproses ({idx+1}/{len(urls)}): {url}")
                            data = await get_video_info(url, api)
                            
                            if "error" in data:
                                failed.append(data)
                            else:
                                results.append(data)
                            
                            # Update progress UI
                            progress_bar.progress((idx + 1) / len(urls))
                            await asyncio.sleep(delay_time)
                            
                except Exception as e:
                    st.error(f"Sesi Error: {e}")
                
                return results, failed

            # Eksekusi Scraper
            with st.spinner("Mohon tunggu, sedang menghubungi server TikTok..."):
                success_data, failed_data = asyncio.run(run_scraper())
            
            st.divider()
            
            # --- 5. HASIL & DOWNLOAD ---
            if success_data:
                st.subheader("📊 Hasil Scraping")
                df_final = pd.DataFrame(success_data)
                st.dataframe(df_final)
                
                # Konversi hasil ke Excel dalam memori
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Data_TikTok')
                    if failed_data:
                        pd.DataFrame(failed_data).to_excel(writer, index=False, sheet_name='Gagal')
                
                st.download_button(
                    label="📥 Download Hasil (.xlsx)",
                    data=output.getvalue(),
                    file_name=f"hasil_tiktok_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            if failed_data:
                with st.expander("⚠️ Lihat Video yang Gagal"):
                    st.table(pd.DataFrame(failed_data))
