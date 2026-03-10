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
    page_title="TikTok Tracker",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
.stApp { background: #F0F2F8 !important; }

[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E4E7EF !important;
}
[data-testid="stSidebar"] > div { padding-top: 1.5rem; }

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }

.topbar {
    display: flex; align-items: center; gap: 0.5rem;
    padding: 0 0 1.5rem 0;
    font-size: 0.82rem; color: #9199B1; font-weight: 500;
}
.topbar .sep { color: #C8CEDF; margin: 0 0.2rem; }
.topbar .active { color: #1A1D2E; font-weight: 700; }

.page-title {
    font-size: 2rem; font-weight: 800; color: #1A1D2E;
    letter-spacing: -0.03em; line-height: 1.15; margin-bottom: 0.2rem;
}
.page-subtitle { font-size: 0.82rem; color: #9199B1; font-weight: 500; margin-bottom: 1.8rem; }

.card-grid {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 0.9rem; margin-bottom: 0.9rem;
}
.card-grid-3 {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 0.9rem; margin-bottom: 1rem;
}
.metric-card {
    background: #FFFFFF; border-radius: 16px;
    padding: 1.2rem 1.4rem; border: 1px solid #E8ECF4;
    display: flex; align-items: flex-start; gap: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.2s ease, transform 0.2s ease;
    animation: fadeUp 0.35s ease both;
}
.metric-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); transform: translateY(-1px); }
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.card-icon {
    width: 40px; height: 40px; border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.05rem; flex-shrink: 0;
}
.icon-purple { background: #EDE9FF; }
.icon-orange { background: #FFF1E6; }
.icon-blue   { background: #E6F0FF; }
.icon-green  { background: #E6FAF2; }
.icon-red    { background: #FFE9EC; }
.icon-amber  { background: #FFF8E1; }
.icon-pink   { background: #FFE9F6; }
.icon-teal   { background: #E6FAF8; }
.icon-indigo { background: #EDEFFF; }

.card-body { flex: 1; min-width: 0; }
.card-label {
    font-size: 0.68rem; font-weight: 700; color: #9199B1;
    letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 0.2rem;
}
.card-value {
    font-size: 1.65rem; font-weight: 800; color: #1A1D2E;
    line-height: 1.15; letter-spacing: -0.02em;
}
.card-sub { font-size: 0.72rem; color: #B0B8CF; font-weight: 500; margin-top: 0.12rem; }

.stButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 0.82rem !important;
    background: #7C3AED !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    padding: 0.55rem 1.4rem !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.25) !important;
    transition: all 0.15s !important;
}
.stButton > button:hover {
    background: #6D28D9 !important;
    box-shadow: 0 4px 16px rgba(124,58,237,0.35) !important;
    transform: translateY(-1px) !important;
}
.stDownloadButton > button {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-weight: 700 !important; font-size: 0.82rem !important;
    background: transparent !important; color: #22C55E !important;
    border: 1.5px solid #22C55E !important; border-radius: 10px !important;
    padding: 0.5rem 1.2rem !important; transition: all 0.15s !important;
}
.stDownloadButton > button:hover { background: #F0FDF4 !important; }

.section-label {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 0.08em;
    text-transform: uppercase; color: #9199B1;
}

.creator-table {
    background: #FFFFFF; border-radius: 16px;
    border: 1px solid #E8ECF4; overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.table-header {
    display: grid;
    grid-template-columns: 2.5fr 1fr 1fr 1fr 1.5fr 1fr;
    padding: 0.7rem 1.4rem; border-bottom: 1px solid #F0F2F8;
    background: #FAFBFD;
}
.table-header span {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.08em; text-transform: uppercase; color: #9199B1;
}
.table-footer {
    padding: 0.8rem 1.4rem; text-align: center;
    font-size: 0.73rem; color: #B0B8CF; font-weight: 500;
    border-top: 1px solid #F0F2F8; background: #FAFBFD;
}

.stTextInput > div > div > input, .stPasswordInput > div > div > input {
    background: #FFFFFF !important; border: 1.5px solid #E4E7EF !important;
    border-radius: 10px !important; color: #1A1D2E !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.85rem !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.1) !important;
}

.stProgress > div > div > div {
    background: linear-gradient(90deg, #7C3AED, #A78BFA) !important;
    border-radius: 999px !important;
}
.stProgress > div > div { background: #E8ECF4 !important; border-radius: 999px !important; }

[data-testid="stFileUploader"] {
    background: #FFFFFF !important; border: 1.5px dashed #C4C9DC !important;
    border-radius: 14px !important; transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover { border-color: #7C3AED !important; }

.stSuccess > div {
    background: #F0FDF4 !important; border: 1px solid #BBF7D0 !important;
    border-radius: 12px !important; color: #15803D !important;
}
.stError > div {
    background: #FFF1F2 !important; border: 1px solid #FECDD3 !important;
    border-radius: 12px !important;
}
.stInfo > div {
    background: #F5F3FF !important; border: 1px solid #DDD6FE !important;
    border-radius: 12px !important; color: #6D28D9 !important;
}

.streamlit-expanderHeader {
    background: #FFFFFF !important; border: 1px solid #E8ECF4 !important;
    border-radius: 12px !important; color: #1A1D2E !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important; font-weight: 600 !important;
}
[data-testid="stDataFrame"] {
    border-radius: 14px !important; border: 1px solid #E8ECF4 !important; overflow: hidden !important;
}
hr { border: none !important; border-top: 1px solid #E8ECF4 !important; margin: 1.5rem 0 !important; }
label {
    font-size: 0.72rem !important; font-weight: 700 !important;
    color: #9199B1 !important; letter-spacing: 0.06em !important; text-transform: uppercase !important;
}
.log-box {
    background: #F8F9FC; border: 1px solid #E8ECF4; border-radius: 12px;
    padding: 0.9rem 1.1rem; font-size: 0.78rem; color: #6B7494;
    font-family: 'Fira Code', monospace; max-height: 180px; overflow-y: auto; line-height: 1.8;
}
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #D1D5E8; border-radius: 999px; }

.sidebar-logo { padding: 0 0.5rem 1.5rem 0.5rem; border-bottom: 1px solid #F0F2F8; margin-bottom: 1.5rem; }
.sidebar-logo-title { font-size: 1.15rem; font-weight: 800; color: #1A1D2E; letter-spacing: -0.02em; }
.sidebar-logo-sub {
    font-size: 0.65rem; color: #9199B1; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase; margin-top: 0.15rem;
}
.token-status {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #F0FDF4; color: #16A34A; border: 1px solid #BBF7D0;
    border-radius: 999px; padding: 0.2rem 0.7rem;
    font-size: 0.7rem; font-weight: 700; margin-top: 0.5rem;
}
.dot { width:6px; height:6px; border-radius:50%; background:#22C55E; display:inline-block; }
</style>
""", unsafe_allow_html=True)


# --- BROWSER SETUP ---
@st.cache_resource(show_spinner=False)
def setup_browser():
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], capture_output=True)
    return True

setup_browser()


# --- UTILITIES ---
def safe_int(v):
    try: return 0 if v is None else int(v)
    except: return 0

def fmt(n):
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    if n >= 1_000: return f"{n/1_000:.1f}K"
    return str(n)

def get_hashtags(text_extra):
    if not text_extra: return ""
    return ", ".join(h.get("hashtagName") for h in text_extra if h.get("hashtagName"))


# --- SCRAPING ---
async def get_video_info(url, api):
    try:
        info = await api.video(url=url).info()
        if not info:
            return {"video_url": url, "error": "No data returned"}
        author = info.get("author", {})
        author_stats = info.get("authorStats", {})
        stats = info.get("stats", {})
        stats_v2 = info.get("statsV2", {})
        music = info.get("music", {})
        video_data = info.get("video", {})
        try:
            fmt_time = datetime.fromtimestamp(int(info.get("createTime", 0))).strftime("%Y-%m-%d %H:%M")
        except:
            fmt_time = "N/A"
        return {
            "video_url": url, "create_time": fmt_time,
            "video_id": info.get("id") or video_data.get("id"),
            "author_id": author.get("id"), "unique_id": author.get("uniqueId"),
            "nickname": author.get("nickname"), "music_title": music.get("title"),
            "is_copyrighted": music.get("isCopyrighted"), "play_url": video_data.get("playAddr"),
            "author_name": music.get("authorName"), "hashtags": get_hashtags(info.get("textExtra")),
            "follower_count": safe_int(author_stats.get("followerCount")),
            "heart_count": safe_int(author_stats.get("heart")),
            "video_count": safe_int(author_stats.get("videoCount")),
            "like_count": safe_int(stats.get("diggCount")),
            "comment_count": safe_int(stats.get("commentCount")),
            "play_count": safe_int(stats.get("playCount")),
            "collect_count": safe_int(stats_v2.get("collectCount") or stats.get("collectCount")),
            "share_count": safe_int(stats.get("shareCount")),
            "repost_count": safe_int(stats_v2.get("repostCount") or stats.get("repostCount")),
            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    except Exception as e:
        return {"video_url": url, "error": str(e)}


async def run_scraper(video_urls, ms_token, pb, st_text, log_area):
    results, failed, logs = [], [], []
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3, browser="chromium")
        for idx, url in enumerate(video_urls):
            short = url[:55] + "…" if len(url) > 55 else url
            st_text.markdown(
                f'<div class="section-label">Processing {idx+1} / {len(video_urls)}</div>'
                f'<div style="font-size:0.78rem;color:#9199B1;margin-top:0.2rem;">{short}</div>',
                unsafe_allow_html=True
            )
            data = await get_video_info(url, api)
            if "error" in data:
                failed.append(data)
                logs.append(f'<span style="color:#DC2626;">✗ [{idx+1}]</span> {data.get("error","Unknown")}')
            else:
                results.append(data)
                logs.append(f'<span style="color:#16A34A;">✓ [{idx+1}]</span> @{data.get("unique_id","?")} · {fmt(data.get("play_count",0))} plays')
            log_area.markdown('<div class="log-box">' + "<br>".join(logs[-10:]) + '</div>', unsafe_allow_html=True)
            pb.progress((idx + 1) / len(video_urls))
            await asyncio.sleep(2)
    return results, failed


# ══════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-logo-title">🎵 TikTrack</div>
            <div class="sidebar-logo-sub">Affiliate Tracker Pro</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-bottom:0.5rem;">MS Token</div>', unsafe_allow_html=True)
    token = st.text_input(
        "MS Token", type="password",
        value="hu02L0FHNzvsCOzu44TKmOLTeRdHzhKw7ezMAu_Rz_fs2zjXGDzxd8NHd50pKOU5CDYRP3NAa-6Frha4XeU4hiM1yKpuJv5KvHRB1n6JuPPZ2thX5b94E4A-iT6avWkzgrn73ku_9xy9UbaUNbSED8d7y3M=",
        label_visibility="collapsed"
    )
    if token:
        st.markdown('<div class="token-status"><div class="dot"></div>&nbsp;Token Active</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("How to get MS Token"):
        st.markdown("""
        1. Open **TikTok** in browser & log in
        2. Open **DevTools** → Application tab
        3. Cookies → `tiktok.com`
        4. Find `msToken` → copy the value
        """)


# ══════════════════════════════════
#  MAIN
# ══════════════════════════════════
st.markdown("""
    <div class="topbar">
        <span>← Back</span>
        <span class="sep">|</span>
        <span>Affiliate Tracker</span>
        <span class="sep">›</span>
        <span class="active">TikTok Scraper</span>
    </div>
    <div class="page-title">TikTok Scraper</div>
    <div class="page-subtitle">Created Mar 10, 2026</div>
""", unsafe_allow_html=True)

# Upload
st.markdown('<div class="section-label" style="margin-bottom:0.5rem;">Upload Input File</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"], label_visibility="collapsed")

# ── NO FILE ──
if not uploaded_file:
    st.markdown("""
        <div class="card-grid">
            <div class="metric-card">
                <div class="card-icon icon-purple">👥</div>
                <div class="card-body">
                    <div class="card-label">Total Creators</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">0 active</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-orange">📦</div>
                <div class="card-body">
                    <div class="card-label">Samples Sent</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">delivered or received</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-blue">🏠</div>
                <div class="card-body">
                    <div class="card-label">Direct / MCN</div>
                    <div class="card-value">0/0</div>
                    <div class="card-sub">contact type</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-green">📈</div>
                <div class="card-body">
                    <div class="card-label">Active</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">creators posting</div>
                </div>
            </div>
        </div>
        <div class="card-grid-3">
            <div class="metric-card">
                <div class="card-icon icon-indigo">🎬</div>
                <div class="card-body">
                    <div class="card-label">Total Short Videos</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">locked (all)</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-green">✅</div>
                <div class="card-body">
                    <div class="card-label">Posted</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">short videos</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-amber">⏳</div>
                <div class="card-body">
                    <div class="card-label">Not Posted</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">short videos</div>
                </div>
            </div>
        </div>
        <div class="card-grid-3">
            <div class="metric-card">
                <div class="card-icon icon-pink">📡</div>
                <div class="card-body">
                    <div class="card-label">Live Stream Locks</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">contracts</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-red">🔴</div>
                <div class="card-body">
                    <div class="card-label">Total Sessions</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">live sessions locked</div>
                </div>
            </div>
            <div class="metric-card">
                <div class="card-icon icon-teal">⭐</div>
                <div class="card-body">
                    <div class="card-label">Exclusive Lives</div>
                    <div class="card-value">0</div>
                    <div class="card-sub">exclusive streams</div>
                </div>
            </div>
        </div>
        <div class="creator-table">
            <div class="table-header">
                <span>Creator</span>
                <span>Phone (WA)</span>
                <span>Contact</span>
                <span>Samples</span>
                <span>Videos &amp; Streams</span>
                <span>Actions</span>
            </div>
            <div style="text-align:center;padding:2.5rem;color:#B0B8CF;font-size:0.82rem;font-weight:500;">
                No creators yet — upload an Excel file to begin scraping.
            </div>
            <div class="table-footer">0 of 0 creators</div>
        </div>
    """, unsafe_allow_html=True)

# ── FILE LOADED ──
else:
    try:
        df_in = pd.read_excel(uploaded_file)
        if "video_url" not in df_in.columns:
            st.error("❌ Column `video_url` not found. Please check your Excel file.")
            st.stop()

        urls = df_in["video_url"].dropna().tolist()
        est  = round(len(urls) * 5 / 60, 1)

        st.markdown(f"""
            <div class="card-grid">
                <div class="metric-card">
                    <div class="card-icon icon-purple">👥</div>
                    <div class="card-body">
                        <div class="card-label">Total Creators</div>
                        <div class="card-value">{len(urls)}</div>
                        <div class="card-sub">URLs ready</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="card-icon icon-orange">📋</div>
                    <div class="card-body">
                        <div class="card-label">Total Rows</div>
                        <div class="card-value">{len(df_in)}</div>
                        <div class="card-sub">in uploaded file</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="card-icon icon-amber">⏱️</div>
                    <div class="card-body">
                        <div class="card-label">Est. Duration</div>
                        <div class="card-value">{est}m</div>
                        <div class="card-sub">approximate time</div>
                    </div>
                </div>
                <div class="metric-card">
                    <div class="card-icon icon-indigo">📊</div>
                    <div class="card-body">
                        <div class="card-label">Output Columns</div>
                        <div class="card-value">21</div>
                        <div class="card-sub">data fields</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.expander(f"👁️ Preview — {len(urls)} URLs loaded"):
            st.dataframe(df_in[["video_url"]].head(20), use_container_width=True, hide_index=True)

        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            start = st.button("🚀 Start Scraping", use_container_width=True)

        if start:
            if not token:
                st.error("⛔ Please enter your MS Token in the sidebar.")
                st.stop()

            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown('<div class="section-label" style="margin-bottom:0.8rem;">⚡ Live Progress</div>', unsafe_allow_html=True)

            p_col, s_col = st.columns([2, 3])
            with p_col: pb = st.progress(0)
            with s_col: st_text = st.empty()
            log_area = st.empty()

            with st.spinner(""):
                res, fail = asyncio.run(run_scraper(urls, token, pb, st_text, log_area))

            st.markdown("<br>", unsafe_allow_html=True)
            rate = round(len(res) / len(urls) * 100) if urls else 0

            st.markdown(f"""
                <div class="card-grid-3">
                    <div class="metric-card">
                        <div class="card-icon icon-green">✅</div>
                        <div class="card-body">
                            <div class="card-label">Successful</div>
                            <div class="card-value" style="color:#16A34A;">{len(res)}</div>
                            <div class="card-sub">videos scraped</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="card-icon icon-red">❌</div>
                        <div class="card-body">
                            <div class="card-label">Failed</div>
                            <div class="card-value" style="color:#DC2626;">{len(fail)}</div>
                            <div class="card-sub">errors encountered</div>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="card-icon icon-purple">📈</div>
                        <div class="card-body">
                            <div class="card-label">Success Rate</div>
                            <div class="card-value">{rate}%</div>
                            <div class="card-sub">completion</div>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                if res:  pd.DataFrame(res).to_excel(writer, index=False, sheet_name="Success")
                if fail: pd.DataFrame(fail).to_excel(writer, index=False, sheet_name="Failed")

            dl1, _ = st.columns([1, 4])
            with dl1:
                st.download_button(
                    "📥 Export XLSX", data=output.getvalue(),
                    file_name=f"tiktok_results_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            if res:
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-label" style="margin-bottom:0.6rem;">Results Preview</div>', unsafe_allow_html=True)
                df_res = pd.DataFrame(res)
                show  = ["unique_id","nickname","play_count","like_count","comment_count","share_count","follower_count","hashtags","create_time"]
                avail = [c for c in show if c in df_res.columns]
                st.dataframe(df_res[avail], use_container_width=True, hide_index=True, height=380)

            if fail:
                with st.expander(f"⚠️ {len(fail)} Failed URLs"):
                    st.dataframe(pd.DataFrame(fail), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error reading file: {e}")
