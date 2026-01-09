import streamlit as st
import asyncio
import pandas as pd
import os
from TikTokApi import TikTokApi
from datetime import datetime
import io

# --- Konfigurasi Halaman Streamlit ---
st.set_page_config(page_title="TikTok Scraper Tool", page_icon="📊")

st.title("📱 TikTok Video Scraper")
st.markdown("""
Upload file Excel berisi kolom **video_url**, klik proses, dan download hasilnya setelah selesai.
""")

# Masukkan ms_token kamu di sini
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info:
            raise ValueError("Data tidak ditemukan atau URL salah")

        return {
            "video_url": url,
            "create_time": info.get("createTime"),
            "video_id": info.get("video", {}).get("id"),
            "author_id": info.get("author", {}).get("id"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "nickname": info.get("author", {}).get("nickname"),
            "music_title": info.get("music", {}).get("title"),
            "hashtags": ", ".join([h["hashtagName"] for h in info.get("textExtra", []) if h.get("hashtagName")]),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- Core Logic ---------
async def run_scraping(video_urls):
    results = []
    failed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[MS_TOKEN],
            num_sessions=1,
            sleep_after=2,
            browser="chromium"
        )

        for idx, url in enumerate(video_urls):
            status_text.text(f"Scraping {idx+1}/{len(video_urls)}: {url}")
            data = await get_video_info(url, api)
            
            if "error" not in data:
                results.append(data)
            else:
                failed.append(data)
            
            # Update progress bar
            progress_bar.progress((idx + 1) / len(video_urls))
            
    return results, failed

# --------- UI Layout ---------
uploaded_file = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        df_input = pd.read_excel(uploaded_file, engine='openpyxl')
        
        if "video_url" not in df_input.columns:
            st.error("Kolom 'video_url' tidak ditemukan!")
        else:
            urls = df_input["video_url"].dropna().tolist()
            st.success(f"Ditemukan {len(urls)} URL siap di-scrape.")

            if st.button("Mulai Scraping"):
                # Menjalankan fungsi async di Streamlit
                with st.spinner("Sedang mengambil data dari TikTok..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    results, failed = loop.run_until_complete(run_scraping(urls))

                # --- Bagian Download ---
                st.divider()
                st.subheader("Hasil Scraping")
                
                # Buat Excel di memory (RAM) agar bisa didownload
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    if results:
                        pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Success")
                    if failed:
                        pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Failed")
                
                processed_data = output.getvalue()

                col1, col2 = st.columns(2)
                col1.metric("Berhasil", len(results))
                col2.metric("Gagal", len(failed))

                st.download_button(
                    label="📥 Download Hasil Scraping",
                    data=processed_data,
                    file_name=f"scraped_tiktok_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")
