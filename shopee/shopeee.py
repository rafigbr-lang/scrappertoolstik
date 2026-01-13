import streamlit as st
import requests
import re
import json

st.set_page_config(page_title="Shopee Video Downloader v2", page_icon="🧡")

def get_shopee_video_api(short_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }
    
    try:
        # 1. Ikuti redirect link pendek ke link asli
        response = requests.get(short_url, headers=headers, allow_redirects=True, timeout=10)
        final_url = response.url
        
        # 2. Ambil ID Video dari URL (biasanya setelah /video/)
        # Contoh URL: https://shopee.co.id/video/12345678
        video_id_match = re.search(r'video/(\d+)', final_url)
        if not video_id_match:
            # Coba cari ID di dalam body jika tidak ada di URL
            video_id_match = re.search(r'"item_id":(\d+)', response.text)
            
        if video_id_match:
            video_id = video_id_match.group(1)
            # 3. Gunakan API internal Shopee untuk ambil data video
            # Kita mencoba menebak endpoint API mobile
            api_url = f"https://help.shopee.co.id/api/v1/video/detail?item_id={video_id}"
            # Catatan: Endpoint ini bisa berubah, kita juga bisa scrape via regex di HTML
            
            # Cara Alternatif: Cari link .mp4 langsung di dalam source code halaman
            video_links = re.findall(r'https://cv.shopee.sg/file/[a-zA-Z0-9_-]+', response.text)
            if video_links:
                return video_links[0] # Ambil link video pertama yang ketemu
                
        return "Gagal menemukan link video. Shopee memproteksi halaman ini."
        
    except Exception as e:
        return f"Terjadi kesalahan: {str(e)}"

# --- UI ---
st.title("🧡 Shopee Video Downloader (Lite)")
st.info("Versi ini lebih stabil dan tidak sering error di Streamlit Cloud.")

url_input = st.text_input("Masukkan link id.shp.ee kamu:", placeholder="https://id.shp.ee/...")

if st.button("Ambil Video"):
    if url_input:
        with st.spinner("Sedang mengambil data..."):
            video_link = get_shopee_video_api(url_input)
            
            if "http" in video_link:
                st.success("Berhasil!")
                st.video(video_link)
                st.code(video_link)
            else:
                st.error(video_link)
                st.info("Jika gagal, Shopee mungkin mendeteksi bot. Coba beberapa saat lagi.")
    else:
        st.warning("Isi linknya dulu ya.")
