import streamlit as st
import requests
import re

st.set_page_config(page_title="Shopee Video Fix", page_icon="🧡")

def get_video_v3(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://shopee.co.id/",
    }
    
    try:
        # 1. Resolving short link
        session = requests.Session()
        res = session.get(url, headers=headers, allow_redirects=True)
        final_url = res.url
        
        # 2. Cari Video ID dari URL asli
        # Pola biasanya: shopee.co.id/video/1234567
        video_id = re.search(r'video/(\d+)', final_url)
        
        if not video_id:
            # Jika tidak ada di URL, cari di content
            video_id = re.search(r'"item_id":(\d+)', res.text)

        if video_id:
            v_id = video_id.group(1)
            # 3. Request ke API internal Shopee Video
            api_url = f"https://shopee.co.id/api/v4/video/get_video_detail?item_id={v_id}"
            api_res = session.get(api_url, headers=headers).json()
            
            # 4. Ekstraksi URL Video dari JSON
            # Struktur Shopee biasanya: data -> video_info -> video_list -> url
            video_data = api_res.get('data', {}).get('video_info', {})
            video_url = video_data.get('video_list', [{}])[0].get('main_url')
            
            if video_url:
                return video_url
        
        # Backup: Cari regex mp4 di HTML mentah jika API gagal
        raw_mp4 = re.search(r'https://cv.shopee.sg/file/[a-zA-Z0-9_-]+', res.text)
        if raw_mp4:
            return raw_mp4.group(0)

        return None
    except Exception as e:
        return f"Error: {e}"

st.title("🧡 Shopee Video Downloader (Final Fix)")

link = st.text_input("Masukkan link id.shp.ee:")

if st.button("Ambil Video"):
    if link:
        with st.spinner("Sedang menembus proteksi..."):
            result = get_video_v3(link)
            if result and result.startswith("http"):
                st.success("Berhasil!")
                st.video(result)
                st.code(result)
            else:
                st.error("Shopee mendeteksi akses dari server Cloud (IP Blocked).")
                st.info("Saran: Jalankan script ini di Laptop/PC sendiri (Localhost) agar IP tidak dianggap bot oleh Shopee.")
