import streamlit as st
import asyncio
import pandas as pd
import os
from TikTokApi import TikTokApi
from datetime import datetime
import io

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="TikTok Integrator Multi-File", layout="wide")

st.title("📊 TikTok Scraper & Multi-File GMV Integrator")

# Masukkan ms_token kamu di sini
MS_TOKEN = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='

# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if "author" not in info: raise ValueError("Data tidak ditemukan")
        
        return {
            "video_url": url,
            "unique_id": info.get("author", {}).get("uniqueId"),
            "nickname": info.get("author", {}).get("nickname"),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}

# --------- UI Tabs ---------
tab1, tab2 = st.tabs(["🚀 Step 1: Scrape TikTok", "🔗 Step 2: Integrate GMV Data"])

with tab1:
    st.subheader("Ambil Data dari TikTok")
    uploaded_scrape = st.file_uploader("Upload Daftar URL TikTok (.xlsx)", type=["xlsx"])
    
    if uploaded_scrape:
        df_input = pd.read_excel(uploaded_scrape)
        if "video_url" in df_input.columns:
            urls = df_input["video_url"].dropna().tolist()
            st.info(f"Ditemukan {len(urls)} URL.")
            
            if st.button("Mulai Scraping"):
                with st.spinner("Sedang scraping..."):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    async def run_scrape():
                        results = []
                        async with TikTokApi() as api:
                            await api.create_sessions(ms_tokens=[MS_TOKEN], num_sessions=1, sleep_after=2)
                            for url in urls:
                                res = await get_video_info(url, api)
                                results.append(res)
                        return results
                    
                    final_results = loop.run_until_complete(run_scrape())
                    st.session_state['scraped_df'] = pd.DataFrame(final_results)
                    st.success("Scraping Selesai! Silahkan lanjut ke Tab 'Integrate GMV Data'.")
        else:
            st.error("Kolom 'video_url' tidak ditemukan!")

with tab2:
    st.subheader("Gabungkan dengan Data GMV (Multiple Files)")
    # Mengaktifkan accept_multiple_files=True
    uploaded_gmv_files = st.file_uploader(
        "Upload Semua File GMV (.xlsx)", 
        type=["xlsx"], 
        accept_multiple_files=True
    )
    
    if uploaded_gmv_files and 'scraped_df' in st.session_state:
        all_gmv_data = []
        
        for file in uploaded_gmv_files:
            df_temp = pd.read_excel(file)
            # Membersihkan data sesuai permintaan:
            # 1. Hapus kolom yang mengandung kata 'Refunded'
            cols_to_keep = [c for c in df_temp.columns if 'refunded' not in c.lower()]
            df_temp = df_temp[cols_to_keep]
            
            # 2. Opsional: Hapus baris jika ada status 'Refunded' di kolom status
            if 'Status' in df_temp.columns:
                df_temp = df_temp[df_temp['Status'].astype(str).str.lower() != 'refunded']
                
            all_gmv_data.append(df_temp)
        
        # Gabungkan semua file GMV menjadi satu DataFrame
        df_gmv_combined = pd.concat(all_gmv_data, ignore_index=True)
        st.success(f"Berhasil menggabungkan {len(uploaded_gmv_files)} file GMV.")

        if st.button("Integrasikan Data"):
            df_scrape = st.session_state['scraped_df']
            
            # Pastikan kolom matching bersih dari spasi
            df_scrape['unique_id'] = df_scrape['unique_id'].astype(str).str.strip()
            df_gmv_combined['creator name'] = df_gmv_combined['creator name'].astype(str).str.strip()
            
            # Merging
            df_final = pd.merge(
                df_scrape, 
                df_gmv_combined, 
                left_on='unique_id', 
                right_on='creator name', 
                how='left'
            )
            
            st.write("Pratinjau Hasil Akhir:")
            st.dataframe(df_final.head(10))
            
            # Download Button
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_final.to_excel(writer, index=False)
            
            st.download_button(
                label="📥 Download Hasil Akhir Terintegrasi",
                data=output.getvalue(),
                file_name=f"integrated_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    elif not uploaded_gmv_files:
        st.info("Silahkan upload satu atau lebih file GMV.")
    elif 'scraped_df' not in st.session_state:
        st.warning("Data scraping belum ada. Silahkan selesaikan Step 1.")
