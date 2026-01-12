import argparse
from TikTokApi import TikTokApi
import pandas as pd
import asyncio
import os
import sys
import logging
from datetime import datetime

# Suppress TikTokApi logger
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)

# Masukkan ms_token kamu di sini
ms_token = 'hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M='


# --------- Scraping Helper ---------
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()

        if "author" not in info or "authorStats" not in info or "stats" not in info:
            raise ValueError("Missing author or stats data")

        scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "video_url": url,
            "create_time": info.get("createTime"),
            "video_id": info.get("video", {}).get("id"),
            "author_id": info.get("author", {}).get("id"),
            "unique_id": info.get("author", {}).get("uniqueId"),
            "nickname": info.get("author", {}).get("nickname"),
            "music_title": info.get("music", {}).get("title"),
            "is_copyrighted": info.get("music", {}).get("isCopyrighted"),
            "play_url": info.get("video", {}).get("playAddr"),
            "author_name": info.get("music", {}).get("authorName"),
            "hashtags": ", ".join([h["hashtagName"] for h in info.get("textExtra", []) if h.get("hashtagName")]),
            "follower_count": int(info.get("authorStats", {}).get("followerCount", 0)),
            "heart_count": int(info.get("authorStats", {}).get("heart", 0)),
            "video_count": int(info.get("authorStats", {}).get("videoCount", 0)),
            "like_count": int(info.get("stats", {}).get("diggCount", 0)),
            "comment_count": int(info.get("stats", {}).get("commentCount", 0)),
            "play_count": int(info.get("stats", {}).get("playCount", 0)),
            "collect_count": int(info.get("statsV2", {}).get("collectCount", 0)),
            "share_count": int(info.get("stats", {}).get("shareCount", 0)),
            "repost_count": int(info.get("statsV2", {}).get("repostCount", 0)),
            "scraped_at": scraped_at
        }

    except Exception as e:
        print(f"❌ Failed to fetch info for {url} | Error: {e}")
        return {"video_url": url, "error": str(e)}


# --------- Main Async Function ---------
async def main(input_filename):
    # PATH CONFIGURATION (Sesuaikan folder utama di sini)
    base_dir = r"C:\Users\Ragib\Downloads\scalper"
    input_path = os.path.join(base_dir, "input", input_filename)
    output_dir = os.path.join(base_dir, "output")

    # Buat folder output jika belum ada
    os.makedirs(output_dir, exist_ok=True)

    print(f"--- Memulai Proses Scraping ---")
    print(f"Mencari file di: {input_path}")

    try:
        # Menggunakan engine openpyxl untuk membaca file .xlsx
        df_urls = pd.read_excel(input_path, engine='openpyxl')
    except Exception as e:
        print(f"❌ Gagal membaca file Excel: {e}")
        return

    if "video_url" not in df_urls.columns:
        print("❌ Error: Kolom 'video_url' tidak ditemukan di file Excel!")
        return

    video_urls = df_urls["video_url"].dropna().tolist()

    if not video_urls:
        print("⚠️ File Excel kosong atau tidak ada URL yang valid.")
        return

    output_filename = f"scraped_{os.path.splitext(input_filename)[0]}.xlsx"
    output_path = os.path.join(output_dir, output_filename)

    results = []
    failed = []

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token],
            num_sessions=1,
            sleep_after=3,
            browser=os.getenv("TIKTOK_BROWSER", "chromium")
        )

        for idx, url in enumerate(video_urls, 1):
            print(f"[{idx}/{len(video_urls)}] Scraping: {url}")
            data = await get_video_info(url, api)

            if data and "error" not in data:
                results.append(data)
            else:
                failed.append(data)

    # Simpan hasil ke Excel
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            if results:
                pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Success")
            if failed:
                pd.DataFrame(failed).to_excel(writer, index=False, sheet_name="Failed")
        print(f"\n✅ Scraping selesai!")
        print(f"📁 Hasil disimpan di: {output_path}")
    except Exception as e:
        print(f"❌ Gagal menyimpan file output: {e}")


# --------- Entry Point ---------
if __name__ == "__main__":
    # NAMA FILE INPUT (Ubah di sini jika nama filenya ganti)
    FILE_TARGET = "data scalp.xlsx"

    # Jalankan program
    asyncio.run(main(FILE_TARGET))