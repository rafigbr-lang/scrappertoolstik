import io
import subprocess

# --- SETUP ---
# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
st.set_page_config(page_title="TikTok Scalper Fix", page_icon="✅", layout="wide")
st.set_page_config(page_title="TikTok Scalper Pro", page_icon="📊", layout="wide")

@st.cache_resource
def setup_browser():
@@ -20,48 +20,69 @@ def setup_browser():

setup_browser()

# --- HELPER FUNGSI AMAN ---
# --- UTILITY FUNCTIONS ---
def safe_int(value):
    """Mengonversi nilai ke integer secara aman agar tidak error 'str object'"""
try:
if value is None: return 0
return int(value)
    except (ValueError, TypeError):
    except:
return 0

def get_hashtags(text_extra):
    if not text_extra: return ""
    tags = [h.get("hashtagName") for h in text_extra if h.get("hashtagName")]
    return ", ".join(tags)

# --------- Scraping Helper ---------
async def get_video_info(url, api):
try:
video = api.video(url=url)
info = await video.info()

if not info:
            return {"video_url": url, "error": "Tidak ada respon dari TikTok"}
            return {"video_url": url, "error": "No data returned from TikTok"}

        # Ambil data statistik dengan konversi aman
        stats = info.get("stats", {})
        # Extraction Logic
        author = info.get("author", {})
author_stats = info.get("authorStats", {})
        
        # Konversi waktu buat (createTime bisa berupa string atau int dari TikTok)
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})

        # Date Formatting
raw_time = info.get("createTime", 0)
try:
            create_time_str = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
            formatted_time = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
except:
            create_time_str = "Unknown"
            formatted_time = "N/A"

        # Mapping 21 Kolom yang diminta
return {
"video_url": url,
            "create_time": create_time_str,
            "nickname": info.get("author", {}).get("nickname", "N/A"),
            "unique_id": info.get("author", {}).get("uniqueId", "N/A"),
            "create_time": formatted_time,
            "video_id": info.get("id") or video_data.get("id"),
            "author_id": author.get("id"),
            "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"),
            "music_title": music.get("title"),
            "is_copyrighted": music.get("isCopyrighted"),
            "play_url": video_data.get("playAddr"),
            "author_name": music.get("authorName"),
            "hashtags": get_hashtags(info.get("textExtra")),
"follower_count": safe_int(author_stats.get("followerCount")),
            "heart_count": safe_int(author_stats.get("heart")),
            "video_count": safe_int(author_stats.get("videoCount")),
"like_count": safe_int(stats.get("diggCount")),
"comment_count": safe_int(stats.get("commentCount")),
"play_count": safe_int(stats.get("playCount")),
            "collect_count": safe_int(stats_v2.get("collectCount") or stats.get("collectCount")),
            "share_count": safe_int(stats.get("shareCount")),
            "repost_count": safe_int(stats_v2.get("repostCount") or stats.get("repostCount")),
"scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}
except Exception as e:
        return {"video_url": url, "error": f"Logic Error: {str(e)}"}
        return {"video_url": url, "error": str(e)}

# --------- Scraper Engine ---------
async def run_scraper(video_urls, ms_token):
@@ -73,7 +94,7 @@ async def run_scraper(video_urls, ms_token):
await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")

for idx, url in enumerate(video_urls):
            status_text.write(f"⏳ Memproses {idx+1}/{len(video_urls)}...")
            status_text.write(f"⏳ Processing {idx+1}/{len(video_urls)}: {url}")
data = await get_video_info(url, api)

if "error" in data:
@@ -82,32 +103,40 @@ async def run_scraper(video_urls, ms_token):
results.append(data)

progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(2) # Jeda agar tidak dianggap bot agresif
            await asyncio.sleep(2) 

return results, failed

# --------- UI ---------
st.title("🚀 TikTok Scalper Dashboard (Fixed Version)")
# --------- UI STREAMLIT ---------
st.title("🚀 TikTok Scalper Dashboard")

with st.sidebar:
    st.header("Settings")
token = st.text_input("MS Token", type="password", value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=")
    st.info("Input file Excel harus memiliki kolom 'video_url'")

uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])
uploaded_file = st.file_uploader("Upload Input Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    if "video_url" in df.columns:
        urls = df["video_url"].dropna().tolist()
        if st.button("Mulai Scrape"):
    df_in = pd.read_excel(uploaded_file)
    if "video_url" in df_in.columns:
        urls = df_in["video_url"].dropna().tolist()
        st.success(f"Ready to scrape {len(urls)} videos")
        
        if st.button("Start Scraping"):
res, fail = asyncio.run(run_scraper(urls, token))

            # Export
            # Create Excel output
output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if res: pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Berhasil")
                if fail: pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Gagal")
                if res: pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Success")
                if fail: pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Failed")
            
            st.divider()
            st.download_button("📥 Download Scraped Data", output.getvalue(), file_name="tiktok_full_results.xlsx")

            st.success("Selesai!")
            st.download_button("📥 Download Hasil", output.getvalue(), file_name="hasil_tiktok.xlsx")
            if res: st.dataframe(pd.DataFrame(res))
            if fail: st.error("Beberapa URL gagal, cek file download."); st.dataframe(pd.DataFrame(fail))
            if res:
                st.subheader("Results Preview")
                st.dataframe(pd.DataFrame(res))
    else:
        st.error("Column 'video_url' not found!")
