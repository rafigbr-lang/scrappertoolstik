import streamlit as st
from playwright.sync_api import sync_playwright
import subprocess
import time

# Fungsi instalasi browser
def install_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Gagal menginstal browser: {e}")

def scrape_shopee_video(url):
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        
        # Menggunakan User Agent Mobile agar lebih ringan
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-S901B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            viewport={'width': 360, 'height': 800}
        )
        
        page = context.new_page()
        
        try:
            # 1. Buka URL (ini akan menangani redirect dari id.shp.ee secara otomatis)
            st.info("Membuka link dan menunggu pengalihan...")
            page.goto(url, wait_until="commit", timeout=60000)
            
            # 2. Tunggu sampai network agak tenang
            page.wait_for_load_state("networkidle")
            
            # 3. Scroll sedikit untuk memicu loading video (penting di Shopee)
            page.mouse.wheel(0, 500)
            time.sleep(3)
            
            # 4. Mencari video dengan beberapa selector alternatif
            video_url = None
            selectors = ["video", "video.shopee-video-player__video", "source"]
            
            for selector in selectors:
                el = page.query_selector(selector)
                if el:
                    video_url = el.get_attribute("src")
                    if video_url: break
            
            if video_url:
                return video_url
            else:
                return "Video tidak ditemukan. Coba jalankan ulang."

        except Exception as e:
            return f"Terjadi kesalahan: {str(e)}"
        finally:
            browser.close()

# --- UI STREAMLIT ---
st.set_page_config(page_title="Shopee Video Scraper", page_icon="🎬")

st.title("🎬 Shopee Video Link Extractor")
st.caption("Support link pendek: id.shp.ee")

if 'installed' not in st.session_state:
    with st.spinner("Menyiapkan sistem..."):
        install_playwright_browsers()
        st.session_state['installed'] = True

input_url = st.text_input("Paste Link Shopee Video:", placeholder="https://id.shp.ee/...")

if st.button("Extract Video"):
    if input_url:
        with st.spinner("Sedang mengekstrak video..."):
            video_result = scrape_shopee_video(input_url)
            
            if video_result and video_result.startswith("http"):
                st.success("Berhasil!")
                st.video(video_result)
                st.write("**Link Video Mentah:**")
                st.code(video_result)
            else:
                st.error(video_result)
    else:
        st.warning("Silakan masukkan link terlebih dahulu.")
