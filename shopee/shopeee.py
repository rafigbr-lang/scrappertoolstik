import streamlit as st
from playwright.sync_api import sync_playwright
import os
import subprocess
import time

# Fungsi untuk memastikan browser terinstall di server Streamlit
def install_playwright_browsers():
    try:
        # Cek apakah chromium sudah terinstall
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        st.error(f"Gagal menginstal browser: {e}")

def scrape_shopee_video(url):
    with sync_playwright() as p:
        # Menjalankan browser dengan opsi anti-detection sederhana
        browser = p.chromium.launch(headless=True)
        
        # Menggunakan User Agent mobile agar tampilan lebih ringan dan mudah di-scrape
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            viewport={'width': 360, 'height': 640}
        )
        
        page = context.new_page()
        
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Menunggu elemen video muncul (Shopee butuh waktu loading)
            page.wait_for_selector("video", timeout=20000)
            
            # Memberi jeda ekstra agar source video benar-benar ter-load
            time.sleep(3)
            
            # Mengambil link video
            video_element = page.query_selector("video")
            if video_element:
                video_url = video_element.get_attribute("src")
                return video_url
            else:
                return "Video tidak ditemukan di halaman ini."
        except Exception as e:
            return f"Error saat proses scraping: {str(e)}"
        finally:
            browser.close()

# --- UI STREAMLIT ---
st.set_page_config(page_title="Shopee Video Downloader", page_icon="🧡")

st.title("🧡 Shopee Video Scraper")
st.markdown("""
Aplikasi ini mengambil link langsung (*direct link*) dari Shopee Video menggunakan **Playwright**.
""")

# Tombol inisialisasi untuk pertama kali jalan di Cloud
if 'installed' not in st.session_state:
    with st.spinner("Inisialisasi sistem browser (hanya sekali)..."):
        install_playwright_browsers()
        st.session_state['installed'] = True

video_link = st.text_input("Masukkan URL Shopee Video:", 
                          placeholder="https://shopee.co.id/video/...")

if st.button("Cari Video"):
    if video_link:
        if "shopee.co.id/video" not in video_link:
            st.error("Mohon masukkan URL Shopee Video yang valid.")
        else:
            with st.spinner("Sedang memproses... Mohon tunggu (sekitar 10-15 detik)"):
                result = scrape_shopee_video(video_link)
                
                if result and result.startswith("http"):
                    st.success("Berhasil menemukan video!")
                    
                    # Menampilkan video
                    st.video(result)
                    
                    # Link Download
                    st.write("### Direct Link:")
                    st.code(result)
                    st.markdown(f"[Klik di sini untuk Download]({result})")
                else:
                    st.error(f"Gagal: {result}")
    else:
        st.warning("Masukkan link-nya terlebih dahulu.")
