import streamlit as st
from playwright.sync_api import sync_playwright
import os
import subprocess
import time

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Shopee Video Downloader", page_icon="🧡")

# --- FUNGSI INSTALASI (CRITICAL) ---
def ensure_playwright_installed():
    """Memastikan browser Chromium terpasang di server Streamlit."""
    try:
        # Kita cek apakah chromium ada, jika tidak, kita install
        subprocess.run(["playwright", "install", "chromium"], check=True)
        return True
    except Exception as e:
        st.error(f"Gagal inisialisasi browser: {e}")
        return False

# --- FUNGSI SCRAPER ---
def get_shopee_video(url):
    with sync_playwright() as p:
        # Argumen 'args' sangat penting untuk lingkungan Cloud/Docker
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        
        # Simulasi perangkat mobile (lebih ringan & seringkali bypass proteksi awal)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Linux; Android 13; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
            viewport={'width': 360, 'height': 800}
        )
        
        page = context.new_page()
        
        try:
            # 1. Menuju URL (Menangani redirect id.shp.ee)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # 2. Tunggu sebentar agar redirect selesai sempurna
            time.sleep(5)
            
            # 3. Scroll perlahan untuk memicu pemuatan video player
            page.mouse.wheel(0, 400)
            time.sleep(2)

            # 4. Mencari elemen video
            # Mencoba beberapa selector yang sering digunakan Shopee
            video_url = None
            page.wait_for_selector("video", timeout=15000)
            video_element = page.query_selector("video")
            
            if video_element:
                video_url = video_element.get_attribute("src")
            
            # Jika video_url ketemu tapi tipenya blob, kita ambil link aslinya
            if video_url and video_url.startswith("blob:"):
                # Shopee kadang menyembunyikan link di tag source
                source_element = page.query_selector("video source")
                if source_element:
                    video_url = source_element.get_attribute("src")

            return video_url

        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            browser.close()

# --- TAMPILAN APLIKASI ---
st.title("🧡 Shopee Video Scraper")
st.markdown("Pastikan link dalam format `https://id.shp.ee/...` atau link video Shopee langsung.")

# Tombol Inisialisasi
if 'browser_ready' not in st.session_state:
    if st.button("Step 1: Siapkan Sistem Browser"):
        with st.spinner("Sedang memasang Chromium di server..."):
            if ensure_playwright_installed():
                st.session_state['browser_ready'] = True
                st.success("Sistem Siap! Silakan masukkan link.")
else:
    # Form Input Link
    video_url_input = st.text_input("Link Shopee Video:", placeholder="Paste link di sini...")

    if st.button("Step 2: Ambil Video"):
        if video_url_input:
            with st.spinner("Mengekstrak video (ini memakan waktu 10-20 detik)..."):
                result = get_shopee_video(video_url_input)
                
                if result and result.startswith("http"):
                    st.success("Video Berhasil Ditemukan!")
                    st.video(result)
                    st.write("**Direct Link:**")
                    st.code(result)
                else:
                    st.error(f"Gagal mengambil video. Pesan: {result}")
                    st.info("Tips: Coba klik tombol 'Ambil Video' sekali lagi.")
        else:
            st.warning("Masukkan link-nya dulu bos!")

st.divider()
st.caption("Catatan: Gunakan secara bijak. Beberapa video mungkin diproteksi tinggi oleh Shopee.")
