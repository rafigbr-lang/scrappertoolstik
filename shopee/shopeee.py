import streamlit as st
import requests
import re

def get_shopee_video(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    session = requests.Session()
    try:
        # Redirect link pendek
        res = session.get(url, headers=headers, allow_redirects=True)
        # Cari link video mp4 langsung di source code
        video_links = re.findall(r'https://cv.shopee.sg/file/[a-zA-Z0-9_-]+', res.text)
        if video_links:
            return video_links[0]
        return "Video tidak ditemukan. Coba buka link-nya di browser dulu."
    except Exception as e:
        return f"Error: {e}"

st.title("🧡 Shopee Video Downloader (Local)")
link = st.text_input("Masukkan link id.shp.ee:")

if st.button("Ambil Video"):
    if link:
        with st.spinner("Sedang mengambil video..."):
            result = get_shopee_video(link)
            if "http" in result:
                st.video(result)
                st.success("Berhasil!")
                st.code(result)
            else:
                st.error(result)
