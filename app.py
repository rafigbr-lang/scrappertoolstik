import streamlit as st
from TikTokApi import TikTokApi
import pandas as pd
import asyncio
import os
import sys
import logging
from datetime import datetime
import io
import subprocess

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)

st.set_page_config(
    page_title="TikTok Tracker Pro",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

/* Root Variables */
:root {
    --bg-dark: #0A0A0F;
    --bg-card: #111118;
    --bg-elevated: #1A1A24;
    --accent-pink: #FF2D55;
    --accent-cyan: #00F5FF;
    --accent-purple: #BF5AF2;
    --text-primary: #F0F0F5;
    --text-secondary: #8888AA;
    --border: rgba(255,255,255,0.06);
}

/* Global Reset */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    background-color: var(--bg-dark) !important;
    color: var(--text-primary) !important;
}

.stApp {
    background: var(--bg-dark) !important;
    background-image:
        radial-gradient(ellipse 80% 50% at 10% -10%, rgba(255,45,85,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 110%, rgba(0,245,255,0.05) 0%, transparent 60%) !important;
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: 'Syne', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Page Header */
.hero-header {
    padding: 2rem 0 1.5rem 0;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border);
}

.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 2.8rem;
    font-weight: 800;
    background: linear-gradient(135deg, #FF2D55 0%, #BF5AF2 50%, #00F5FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.03em;
    line-height: 1.1;
    margin: 0;
}

.hero-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
    margin-top: 0.4rem;
    letter-spacing: 0.02em;
}

/* Cards */
.metric-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease;
}

.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--accent-pink), var(--accent-purple), var(--accent-cyan));
    opacity: 0;
    transition: opacity 0.2s ease;
}

.metric-card:hover::before { opacity: 1; }
.metric-card:hover { border-color: rgba(255,255,255,0.12); }

.metric-label {
    font-size: 0.72rem;
    font-weight: 500;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 0.4rem;
}

.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
}

.metric-icon {
    position: absolute;
    top: 1.2rem; right: 1.4rem;
    font-size: 1.4rem;
    opacity: 0.25;
}

/* Upload Zone */
.upload-zone {
    background: var(--bg-card);
    border: 1.5px dashed rgba(255,45,85,0.3);
    border-radius: 20px;
    padding: 3rem 2rem;
    text-align: center;
    transition: border-color 0.2s ease, background 0.2s ease;
}

.upload-zone:hover {
    border-color: rgba(255,45,85,0.6);
    background: rgba(255,45,85,0.03);
}

/* Buttons */
.stButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.05em !important;
    background: linear-gradient(135deg, #FF2D55, #BF5AF2) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.7rem 2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 20px rgba(255,45,85,0.25) !important;
}

.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 30px rgba(255,45,85,0.4) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Download Button */
.stDownloadButton > button {
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    background: transparent !important;
    color: var(--accent-cyan) !important;
    border: 1.5px solid var(--accent-cyan) !important;
    border-radius: 12px !important;
    padding: 0.6rem 1.8rem !important;
    transition: all 0.2s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(0,245,255,0.08) !important;
    box-shadow: 0 0 20px rgba(0,245,255,0.15) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stPasswordInput > div > div > input {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

.stTextInput > div > div > input:focus,
.stPasswordInput > div > div > input:focus {
    border-color: rgba(255,45,85,0.5) !important;
    box-shadow: 0 0 0 2px rgba(255,45,85,0.1) !important;
}

/* Progress Bar */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #FF2D55, #BF5AF2, #00F5FF) !important;
    border-radius: 999px !important;
}

.stProgress > div > div {
    background: var(--bg-elevated) !important;
    border-radius: 999px !important;
}

/* Dataframe */
.stDataFrame {
    border-radius: 16px !important;
    overflow: hidden !important;
    border: 1px solid var(--border) !important;
}

/* Alerts */
.stSuccess {
    background: rgba(0,245,150,0.08) !important;
    border: 1px solid rgba(0,245,150,0.2) !important;
    border-radius: 12px !important;
    color: #00F595 !important;
}

.stError {
    background: rgba(255,45,85,0.08) !important;
    border: 1px solid rgba(255,45,85,0.25) !important;
    border-radius: 12px !important;
}

.stInfo {
    background: rgba(0,245,255,0.06) !important;
    border: 1px solid rgba(0,245,255,0.2) !important;
    border-radius: 12px !important;
    color: var(--accent-cyan) !important;
}

.stWarning {
    background: rgba(255,190,0,0.08) !important;
    border: 1px solid rgba(255,190,0,0.25) !important;
    border-radius: 12px !important;
}

/* Divider */
hr {
    border: none !important;
    border-top: 1px solid var(--border) !important;
    margin: 2rem 0 !important;
}

/* File Uploader */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1.5px dashed rgba(255,45,85,0.3) !important;
    border-radius: 16px !important;
    padding: 1rem !important;
    transition: border-color 0.2s ease;
}

[data-testid="stFileUploader"]:hover {
    border-color: rgba(255,45,85,0.5) !important;
}

/* Section Headers */
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Status badge */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(0,245,150,0.1);
    color: #00F595;
    border: 1px solid rgba(0,245,150,0.2);
    border-radius: 999px;
    padding: 0.25rem 0.8rem;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
}

/* Log area */
.log-container {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-family: 'DM Mono', 'Fira Code', monospace;
    font-size: 0.8rem;
    color: var(--text-secondary);
    max-height: 200px;
    overflow-y: auto;
}

/* Sidebar labels */
[data-testid="stSidebar"] label {
    color: var(--text-secondary) !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* Expander */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border-radius: 12px !important;
    border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
    font-family: 'Syne', sans-serif !important;
}

/* Hide Streamlit branding */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# --- BROWSER SETUP ---
@st.cache_resource(show_spinner=False)
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                   capture_output=True)
    return True

setup_browser()


# --- UTILITY FUNCTIONS ---
def safe_int(value):
    try:
        if value is None: return 0
        return int(value)
    except:
        return 0

def format_number(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def get_hashtags(text_extra):
    if not text_extra: return ""
    tags = [h.get("hashtagName") for h in text_extra if h.get("hashtagName")]
    return ", ".join(tags)


# --- SCRAPING LOGIC ---
async def get_video_info(url, api):
    try:
        video = api.video(url=url)
        info = await video.info()
        if not info:
            return {"video_url": url, "error": "No data returned from TikTok"}

        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})

        raw_time = info.get("createTime", 0)
        try:
            formatted_time = datetime.fromtimestamp(int(raw_time)).strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = "N/A"

        return {
            "video_url": url,
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
        return {"video_url": url, "error": str(e)}


async def run_scraper(video_urls, ms_token, progress_bar, status_text, log_area):
    results, failed = [], []
    logs = []

    async with TikTokApi() as api:
        await api.create_sessions(
            ms_tokens=[ms_token], num_sessions=1,
            sleep_after=3, browser="chromium"
        )

        for idx, url in enumerate(video_urls):
            short_url = url[:60] + "..." if len(url) > 60 else url
            status_text.markdown(
                f'<div class="metric-label">Processing {idx+1} of {len(video_urls)}</div>'
                f'<div style="font-size:0.85rem; color:#8888AA; margin-top:0.2rem;">{short_url}</div>',
                unsafe_allow_html=True
            )

            data = await get_video_info(url, api)

            if "error" in data:
                failed.append(data)
                logs.append(f"✗ [{idx+1}] FAILED — {data.get('error', 'Unknown error')}")
            else:
                results.append(data)
                logs.append(f"✓ [{idx+1}] OK — @{data.get('unique_id', '?')} · {format_number(data.get('play_count', 0))} plays")

            log_area.markdown(
                '<div class="log-container">' +
                "<br>".join(logs[-10:]) +
                '</div>',
                unsafe_allow_html=True
            )
            progress_bar.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(2)

    return results, failed


# ==================== UI ====================

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("""
        <div style="padding: 1rem 0 1.5rem 0;">
            <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800;
                        background:linear-gradient(135deg,#FF2D55,#BF5AF2);
                        -webkit-background-clip:text; -webkit-text-fill-color:transparent;">
                🎵 TikTrack
            </div>
            <div style="font-size:0.72rem; color:#8888AA; letter-spacing:0.1em; margin-top:0.2rem;">
                PRO SCRAPER v2.0
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="metric-label">Authentication</div>', unsafe_allow_html=True)
    token = st.text_input(
        "MS Token",
        type="password",
        value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=",
        label_visibility="collapsed"
    )

    if token:
        st.markdown('<div class="status-badge">● Token Active</div>', unsafe_allow_html=True)
    else:
        st.warning("Enter your MS Token to continue")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="metric-label">How to get MS Token</div>', unsafe_allow_html=True)
    with st.expander("Step-by-step guide"):
        st.markdown("""
        1. Open **TikTok** in your browser
        2. Log in to your account
        3. Open **DevTools** → Application tab
        4. Go to **Cookies** → `tiktok.com`
        5. Find the cookie named `msToken`
        6. Copy its value and paste above
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="metric-label">Requirements</div>', unsafe_allow_html=True)
    st.info("Upload an Excel file with a **`video_url`** column containing TikTok URLs.")


# --- MAIN CONTENT ---

# Header
st.markdown("""
    <div class="hero-header">
        <div class="hero-title">TikTok Tracker Pro</div>
        <div class="hero-subtitle">Extract detailed analytics from TikTok videos at scale</div>
    </div>
""", unsafe_allow_html=True)


# Upload Section
col_upload, col_preview = st.columns([1.2, 1], gap="large")

with col_upload:
    st.markdown('<div class="section-title">📂 Upload Input File</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Drop your Excel file here",
        type=["xlsx"],
        label_visibility="collapsed"
    )

with col_preview:
    st.markdown('<div class="section-title">📋 What we extract</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">🎬 Video ID & URL</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">👤 Author Info</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">❤️ Likes & Comments</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">▶️ Play Count</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">🔁 Reposts & Shares</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">🎵 Music & Copyright</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">🏷️ Hashtags</div>
        <div style="font-size:0.8rem; color:#8888AA; padding:0.4rem 0; border-bottom:1px solid rgba(255,255,255,0.05);">👥 Follower Count</div>
    </div>
    """, unsafe_allow_html=True)


# File Loaded State
if uploaded_file:
    try:
        df_in = pd.read_excel(uploaded_file)

        if "video_url" not in df_in.columns:
            st.error("❌ Column `video_url` not found in your Excel file. Please check the column name.")
            st.stop()

        urls = df_in["video_url"].dropna().tolist()

        st.markdown("<br>", unsafe_allow_html=True)

        # Stats row
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">📋</div>
                    <div class="metric-label">Total URLs</div>
                    <div class="metric-value">{len(urls)}</div>
                </div>""", unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">📊</div>
                    <div class="metric-label">Total Rows</div>
                    <div class="metric-value">{len(df_in)}</div>
                </div>""", unsafe_allow_html=True)

        with m3:
            est_minutes = round(len(urls) * 5 / 60, 1)
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">⏱️</div>
                    <div class="metric-label">Est. Time</div>
                    <div class="metric-value">{est_minutes}m</div>
                </div>""", unsafe_allow_html=True)

        with m4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-icon">📤</div>
                    <div class="metric-label">Output Cols</div>
                    <div class="metric-value">21</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Preview toggle
        with st.expander("👁️ Preview uploaded URLs"):
            st.dataframe(
                df_in[["video_url"]].head(20),
                use_container_width=True,
                hide_index=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Action row
        btn_col, hint_col = st.columns([1, 3])
        with btn_col:
            start = st.button("🚀 Start Scraping", use_container_width=True)
        with hint_col:
            st.markdown(
                '<div style="padding-top:0.7rem; font-size:0.8rem; color:#8888AA;">'
                f'Will process {len(urls)} videos with ~2s delay between requests'
                '</div>',
                unsafe_allow_html=True
            )

        # --- SCRAPING ENGINE ---
        if start:
            if not token:
                st.error("⛔ Please enter your MS Token in the sidebar before scraping.")
                st.stop()

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-title">⚡ Live Progress</div>', unsafe_allow_html=True)

            prog_col, status_col = st.columns([2, 3])
            with prog_col:
                progress_bar = st.progress(0)
            with status_col:
                status_text = st.empty()

            log_area = st.empty()

            with st.spinner(""):
                res, fail = asyncio.run(run_scraper(urls, token, progress_bar, status_text, log_area))

            st.markdown("<br>", unsafe_allow_html=True)

            # Results summary
            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-icon" style="color:#00F595;">✓</div>
                        <div class="metric-label">Successful</div>
                        <div class="metric-value" style="color:#00F595;">{len(res)}</div>
                    </div>""", unsafe_allow_html=True)
            with r2:
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-icon" style="color:#FF2D55;">✗</div>
                        <div class="metric-label">Failed</div>
                        <div class="metric-value" style="color:#FF2D55;">{len(fail)}</div>
                    </div>""", unsafe_allow_html=True)
            with r3:
                rate = round(len(res) / len(urls) * 100) if urls else 0
                st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-icon">📈</div>
                        <div class="metric-label">Success Rate</div>
                        <div class="metric-value">{rate}%</div>
                    </div>""", unsafe_allow_html=True)

            # Build Excel
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if res:
                    pd.DataFrame(res).to_excel(writer, index=False, sheet_name="✅ Success")
                if fail:
                    pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="❌ Failed")

            st.markdown("<br>", unsafe_allow_html=True)

            dl_col, _ = st.columns([1, 3])
            with dl_col:
                st.download_button(
                    "📥 Download Results (.xlsx)",
                    data=output.getvalue(),
                    file_name=f"tiktok_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            if res:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-title">📊 Results Preview</div>', unsafe_allow_html=True)

                df_res = pd.DataFrame(res)
                display_cols = [
                    "unique_id", "nickname", "play_count", "like_count",
                    "comment_count", "share_count", "follower_count", "hashtags", "create_time"
                ]
                available_cols = [c for c in display_cols if c in df_res.columns]

                st.dataframe(
                    df_res[available_cols],
                    use_container_width=True,
                    hide_index=True,
                    height=400
                )

            if fail:
                with st.expander(f"⚠️ View {len(fail)} failed URLs"):
                    st.dataframe(pd.DataFrame(fail), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error reading file: {str(e)}")

else:
    # Empty state
    st.markdown("""
        <div style="text-align:center; padding:3rem 0; color:#8888AA;">
            <div style="font-size:3rem; margin-bottom:1rem; opacity:0.4;">📂</div>
            <div style="font-size:0.9rem;">Upload an Excel file to get started</div>
            <div style="font-size:0.78rem; margin-top:0.4rem; opacity:0.7;">Supported format: .xlsx with a <code>video_url</code> column</div>
        </div>
    """, unsafe_allow_html=True)

# --- CONFIGURATION ---
logging.getLogger("TikTokApi.tiktok").setLevel(logging.CRITICAL)
logging.getLogger("streamlit.runtime.scriptrunner_utils").setLevel(logging.CRITICAL)  # ← add this
logging.getLogger("streamlit.runtime.scriptrunner").setLevel(logging.CRITICAL)        # ← and this
