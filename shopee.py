import streamlit as st
from playwright.sync_api import sync_playwright
import time

def scrape_shopee_video(url):
    with sync_playwright() as p:
        # Membuka browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            st.info("Sedang mengakses halaman...")
            page.goto(url, wait_until="networkidle")
            
            # Beri waktu sedikit untuk video loading
            time.sleep(5)
            
            # Mencari tag video
            video_element = page.query_selector("video")
            if video_element:
                video_url = video_element.get_attribute("src")
                return video_url
            else:
                return None
        except Exception as e:
            return f"Error: {e}"
        finally:
            browser.close()

# --- UI STREAMLIT ---
st.set_page_config(page_title="Shopee Video Downloader", page_icon="🧡")

st.title("🧡 Shopee Video Scraper")
st.write("Masukkan URL Shopee Video untuk mengambil file videonya.")

video_link = st.text_input("Paste Link Shopee Video di sini:", 
                          placeholder="https://shopee.co.id/video/...")

if st.button("Ambil Video"):
    if video_link:
        with st.spinner("Tunggu sebentar, sedang mengambil data..."):
            result = scrape_shopee_video(video_link)
            
            if result and result.startswith("http"):
                st.success("Video ditemukan!")
                st.video(result) # Menampilkan video di Streamlit
                st.code(result, language="text") # Menampilkan URL mentah
                st.download_button("Download Video", data=result, file_name="shopee_video.mp4")
            else:
                st.error("Gagal mengambil video. Pastikan link benar atau coba lagi nanti.")
    else:
        st.warning("Masukkan link-nya dulu ya!")
