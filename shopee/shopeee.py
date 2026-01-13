import streamlit as st
import requests
import re
import pandas as pd

# Konfigurasi Tema Streamlit
st.set_page_config(page_title="Shopee Video Tracker", page_icon="📈", layout="wide")

def get_shopee_stats(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://shopee.co.id/",
        "Accept": "application/json",
    }
    session = requests.Session()
    
    try:
        # 1. Menangani Redirect Link Pendek (id.shp.ee)
        res = session.get(url, headers=headers, allow_redirects=True, timeout=10)
        final_url = res.url
        
        # 2. Ambil Video ID (Item ID)
        video_id = re.search(r'video/(\d+)', final_url)
        if not video_id:
            video_id = re.search(r'"item_id":(\d+)', res.text)
            
        if video_id:
            v_id = video_id.group(1)
            # 3. Panggil API Internal Shopee Detail Video
            api_url = f"https://shopee.co.id/api/v4/video/get_video_detail?item_id={v_id}"
            api_res = session.get(api_url, headers=headers).json()
            
            if api_res.get('data'):
                v_info = api_res['data'].get('video_info', {})
                return {
                    "Status": "Sukses",
                    "Judul": v_info.get('title', 'Tanpa Judul'),
                    "Views": v_info.get('view_count', 0),
                    "Likes": v_info.get('like_count', 0),
                    "Comments": v_info.get('comment_count', 0),
                    "Shares": v_info.get('share_count', 0),
                    "Thumbnail": v_info.get('cover_url', '')
                }
        return {"Status": "Gagal", "Pesan": "Video ID tidak ditemukan. Coba cek link lagi."}
    except Exception as e:
        return {"Status": "Error", "Pesan": str(e)}

# --- Tampilan Dashboard Streamlit ---
st.title("📈 Shopee Video Performance Tracker")
st.markdown("Masukkan link video untuk melihat performa konten secara real-time.")

# Input URL
video_link = st.text_input("Paste Link Shopee Video (id.shp.ee):", placeholder="https://id.shp.ee/...")

if st.button("Cek Statistik"):
    if video_link:
        with st.spinner("Sedang mengambil data dari Shopee..."):
            data = get_shopee_stats(video_link)
