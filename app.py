# streamlit_app_redesign.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
import re
import html

# your existing plotting/data helpers (assumed available)
from steam_api.steam_client import get_owned_df, get_user_data, get_unlocked_achievements
from plots.bar_top_games import get_top_games_plot_plotly
from plots.histogram import get_achievement_hour_histogram_plotly, get_achievement_hour_histogram_plotly_by_year
from plots.radar import get_category_radar_plotly
from plots.donut import get_genre_donut_plotly
from plots.roi_scatter import get_roi_scatter_plot_plotly
from plots.map import get_developers_map_plotly
from plots.race_bar import build_animated_bar_race

# --------------------------
# Theme / colors / CSS
# --------------------------
BG = "#111317"
CARD_BG = "linear-gradient(180deg, #17191d 0%, #0f1113 100%)"
TEXT = "#e4ddeb"
ACCENT = "#66c0f4"
ACCENT2 = "#ffb84c"

st.set_page_config(page_title="Steam Profile — Story Dashboard", page_icon="🎮", layout="wide")

st.markdown(
    f"""
    <style>
    .stApp{{
        background-color: #0a0b0d;
    }}

    .gallery-scroll {{
    max-height: 290px;
    overflow-y: auto;
    padding-right: 10px;
    }}
    .gallery-scroll::-webkit-scrollbar {{
        width: 8px;
    }}
    .gallery-scroll::-webkit-scrollbar-track {{
        background: rgba(255,255,255,0.05);
    }}
    .gallery-scroll::-webkit-scrollbar-thumb {{
        background: rgba(255,255,255,0.2);
        border-radius: 4px;
    }}
    .gallery-scroll::-webkit-scrollbar-thumb:hover {{
        background: rgba(255,255,255,0.3);
    }}
    .gallery-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
        gap: 14px;
        margin-top: 12px;
    }}
    .gallery-item {{
        background: #1f1f1f;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 6px;
        text-align: center;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }}
    .gallery-item:hover {{
        transform: translateY(-4px);
        box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    }}
    .gallery-item img {{
        width: 100%;
        border-radius: 6px;
    }}
    .gallery-title {{
        font-size: 0.78rem;
        color: #ddd;
        margin-top: 6px;
        height: 34px;
        overflow: hidden;
    }}
    .gallery-hours {{
        font-size: 0.7rem;
        color: #bbbbbb;
    }}
    :root {{
        --bg: {BG};
        --card: #14161a;
        --text: {TEXT};
        --accent: {ACCENT};
        --accent2: {ACCENT2};
    }}
    html, body, #root {{
        background: var(--bg);
        color: var(--text);
    }}
    .topbar {{
        display:flex;
        align-items:center;
        gap:12px;
    }}
    .brand {{
        font-size:18px;
        font-weight:700;
        letter-spacing:0.6px;
    }}
    .subtitle {{
        color: #bdbdbd;
        font-size:12px;
        margin-top: -6px;
    }}
    .card {{
        background: {CARD_BG};
        border-radius:12px;
        padding:16px;
        border: 1px solid rgba(255,255,255,0.03);
        box-shadow: 0 4px 18px rgba(0,0,0,0.6);
    }}
    .card-header {{
        background: transparent;
        padding: 10px 14px;
        border-radius:8px;
        margin-bottom:8px;
    }}
    .metric {{
        font-size:20px;
        font-weight:700;
        color: var(--text);
    }}
    .metric-sub {{
        font-size:12px;
        color:#9aa0a6;
    }}
    .story {{
        font-size:14px;
        color:#d6d6d6;
        line-height:1.4;
    }}
    .small-muted {{ color:#9aa0a6; font-size:12px; }}
    .avatar {{
        border-radius:12px;
        width:100%;
        max-width:140px;
        border:1px solid rgba(255,255,255,0.03);
    }}
    .capsule {{ width:100%; border-radius:10px; }}
    .kpi {{ display:flex; gap:12px; align-items:center; }}
    /* make plotly charts look nicely spaced when rendered below card headers */
    .streamlit-chart {{
        margin-top: 8px;
        margin-bottom: 18px;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------
# Helpers
# --------------------------
def safe_dt(ts):
    try:
        return datetime.fromtimestamp(int(ts), ZoneInfo("America/Mexico_City"))
    except Exception:
        return None

@st.cache_data(show_spinner=True)
def load_data(account_id):
    owned = get_owned_df(account_id)
    account = get_user_data(account_id)
    return owned, account

def safe_get(df, col, default=None):
    return df[col] if col in df.columns else pd.Series([default]*len(df), index=df.index)

def render_game_gallery(df):
    if df is None or df.empty:
        st.info("No games match your filters.")
        return

    blocks = []
    for _, row in df.iterrows():
        title_raw = row.get("name", "Unknown title")
        title = html.escape(str(title_raw))
        img = html.escape(str(row.get("capsule_image_path", "") or ""))
        appid = row.get('appid', None)
        minutes = row.get("playtime_forever", 0) or 0
        try:
            minutes = int(minutes)
        except Exception:
            minutes = 0
        hours = round(minutes / 60, 1)

        if appid:
            steam_url = f"https://store.steampowered.com/app/{appid}/"
        else:
            steam_url = "#"

        # create compact block (no leading spaces / newlines)
        block = (
            f'<a href="{steam_url}" target="_blank">'
            '<div class="gallery-item">'
            f'<img src="{img}" alt="{title}">'
            f'<div class="gallery-title">{title}</div>'
            f'<div class="gallery-hours">{hours} hours played</div>'
            '</div>'
        )
        blocks.append(block)

    gallery_html = (
        "<div class='gallery-scroll'>"
        "<div class='gallery-grid'>"
        + "".join(blocks) +
        "</div></div>"
    )

    st.markdown(gallery_html, unsafe_allow_html=True)



# --------------------------
# Header / Input
# --------------------------
st.markdown(
    """
    <div class="topbar">
        <div class="brand">Steam Profile — Story Dashboard</div>
        <div class="subtitle">Fast insights & narrative highlights from your Steam account</div>
    </div>
    """,
    unsafe_allow_html=True,
)

steam_id = str(st.text_input("Enter a SteamID64", placeholder="e.g. 76561198000000000"))
if not steam_id:
    st.info("Enter a SteamID64 to load the profile and insights.")
    st.stop()

# --------------------------
# Load data
# --------------------------
try:
    owned, account = load_data(steam_id)
except Exception as e:
    st.error(f"Could not load Steam data: {e}")
    st.stop()

# --------------------------
# Quick computed insights
# --------------------------
total_playtime_minutes = int(safe_get(owned, "playtime_forever", pd.Series([0])).sum())
total_playtime_hours = round(total_playtime_minutes / 60, 1)

num_games = len(owned.index)
top_game = None
top_playtime_hours = 0
if "playtime_forever" in owned.columns and not owned.empty:
    top = owned.sort_values(by="playtime_forever", ascending=False).reset_index(drop=True)
    top_game = top.iloc[0]
    top_playtime_hours = round(int(top_game["playtime_forever"]) / 60, 1)

# Prepare achievements (safe)
achievements = pd.DataFrame()
try:
    appids = owned["appid"].tolist() if "appid" in owned.columns else []
    achievements_list = []
    # Be conservative — iterating through all apps can be slow; we tolerate failures
    for app_id in appids:
        try:
            a = get_unlocked_achievements(app_id, steam_id)
            achievements_list.append(a)
        except Exception:
            continue
    if len(achievements_list) > 0:
        achievements = pd.concat(achievements_list, ignore_index=True)
        if "unlocktime" in achievements.columns:
            achievements["unlocktime"] = pd.to_datetime(achievements["unlocktime"], unit="s", origin="unix", utc=False)
            achievements["hour"] = achievements["unlocktime"].dt.hour
except Exception:
    achievements = pd.DataFrame()

num_achievements = len(achievements.index) if not achievements.empty else 0

# Playtime peak hour from achievements as a proxy
peak_hour = None
if not achievements.empty and "hour" in achievements.columns:
    try:
        peak_hour = int(achievements["hour"].mode().iloc[0])
    except Exception:
        peak_hour = None

# Favorite genre placeholder
favorite_genre = None
if "genres" in owned.columns and not owned.empty:
    try:
        genres_series = owned["genres"].dropna().astype(str)

        # Clean brackets/quotes robustly
        cleaned = (
            genres_series
            .str.replace(r"[\[\]'\"()]", "", regex=True)  # remove brackets & quotes
            .str.replace(r"\s+", " ", regex=True)        # normalize whitespace
            .str.strip()
        )

        # Split on comma OR semicolon OR simply spaces for weird cases
        all_genres = (
            cleaned
            .str.split(r"[;,]|\s{2,}", regex=True)  # split on , ; or double spaces
            .explode()
            .str.strip()
        )

        # Remove empty strings
        all_genres = all_genres[all_genres != ""]

        if not all_genres.empty:
            favorite_genre = all_genres.value_counts().idxmax()

    except Exception:
        favorite_genre = None

# --------------------------
# Top navigation (tabs)
# --------------------------
tabs = st.tabs(["Overview", "Games", "Achievements", "Developers", "About"])

# --------------------------
# OVERVIEW Tab
# --------------------------
with tabs[0]:
    st.markdown("### Overview — Quick story")
    col1, col2 = st.columns([1, 1.5])

    with col1:
        # Profile card (card used for text/metrics only)
        avatar = account.get("avatarfull", "")
        persona = account.get("personaname", "Unknown")
        lastlogoff = safe_dt(account.get("lastlogoff"))
        created = safe_dt(account.get("timecreated"))

        profile_html = f"""
        <div class='card'>
            <div style="display:flex; gap:16px; align-items:center;">
                <div style="flex:0 0 140px;">
                    <img src="{avatar}" class="avatar" />
                </div>
                <div style="flex:1;">
                    <div style="font-size:18px; font-weight:700;">{persona}</div>
                    <div class="small-muted">Last online: {lastlogoff.strftime('%b %d, %Y at %H:%M') if lastlogoff else 'Unknown'}</div>
                    <div class="small-muted">Member since: {created.strftime('%b %d, %Y') if created else 'Unknown'}</div>
                    <div style="height:8px;"></div>
                    <div class="kpi">                    
                        <div style="min-width:110px;">
                            <div class="metric">{total_playtime_hours}h</div>
                            <div class="metric-sub">Total playtime</div>
                        </div>
                        <div style="min-width:110px;">
                            <div class="metric">{num_games}</div>
                            <div class="metric-sub">Owned games</div>
                        </div>
                        <div style="min-width:110px;">
                            <div class="metric">{num_achievements}</div>
                            <div class="metric-sub">Achievements unlocked</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(profile_html, unsafe_allow_html=True)

        # Short narrative / story card
        story_lines = []
        if top_game is not None:
            name = top_game.get("name", "Unknown")
            story_lines.append(f"You spend most of your playtime on {name} ({top_playtime_hours} hours).")
        if favorite_genre:
            story_lines.append(f"Your most frequent genre is {favorite_genre}.")
        if peak_hour is not None:
            ampm = "AM" if peak_hour < 12 else "PM"
            hr12 = peak_hour if 1 <= peak_hour <= 12 else (peak_hour - 12 if peak_hour > 12 else 12)
            story_lines.append(f"Most achievements are unlocked around {hr12} {ampm}, so you're likely gaming in the {'evening' if peak_hour >= 18 or peak_hour < 6 else 'daytime'}.")
        if not story_lines:
            story_lines.append("No strong signals available yet — try exploring the Games and Achievements tabs for more details.")

        story_html = "<div class='card'><div class='story'>" + "<br>".join(story_lines) + "</div></div>"
        st.markdown(story_html, unsafe_allow_html=True)

        #Fav game thumbnail
        img_url = top_game.get('capsule_image_path')
        content = f"""
            <div class='card' style='text-align:center; padding:10px;'>
                <img src="{img_url}" style="width:240px; border-radius:8px;" />
            </div>
            """
        st.markdown(content, unsafe_allow_html=True)


    with col2:
        # Card header (no plot inside)
        st.markdown("<div class='card-header card'><strong>Your top played games</strong></div>", unsafe_allow_html=True)

        # Plot OUTSIDE the card header — this prevents Streamlit iframe escaping the card
        try:
            top_df = owned.sort_values(by="playtime_forever", ascending=False).head(10)
            fig = get_top_games_plot_plotly(top_df)
            st.plotly_chart(fig, use_container_width=True)
            # micro-story as small muted text (keeps it visually tied to chart)
            if top_game is not None:
                st.markdown(f"<div class='small-muted'>Top game: <b>{top_game.get('name', 'Unknown')}</b> — {top_playtime_hours} hours. Top 3 games represent {round((top_df['playtime_forever'].head(3).sum() / (owned['playtime_forever'].sum() or 1))*100,1)}% of your total playtime.</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error("Could not render top games plot.")
            st.write(e)

# --------------------------
# GAMES Tab
# --------------------------
with tabs[1]:
    st.markdown("### Games — Dive into individual titles")
    with st.container():
        left, right = st.columns([0.6, 0.4])

        with left:
            # ROI Scatter header
            st.markdown("<div class='card-header card'><strong>Playtime distribution & ROI</strong></div>", unsafe_allow_html=True)
            try:
                fig = get_roi_scatter_plot_plotly(owned)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("<div class='small-muted'>Scatter shows playtime vs. cost — great for spotting bargains (high playtime, low price).</div>", unsafe_allow_html=True)
            except Exception:
                st.error("ROI scatter not available.")

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)


        with right:
            st.markdown("<div class='card'><strong>Quick game filters</strong></div>", unsafe_allow_html=True)
            # filters - basic ones that shouldn't depend on columns
            min_play = int(st.slider("Min playtime (minutes)", min_value=0, max_value=int(owned["playtime_forever"].max() if "playtime_forever" in owned.columns else 10000), value=0))
            filtered = owned[owned["playtime_forever"] >= min_play] if "playtime_forever" in owned.columns else owned
            st.markdown(
                f"<div class='card small-muted'>Showing {len(filtered)} games with ≥ {min_play} minutes played.</div>", 
                unsafe_allow_html=True
            )

            render_game_gallery(filtered)

            st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)

    with st.container():
        left, right = st.columns([0.5, 0.5])

        with left:
            # Radar header
            st.markdown("<div class='card-header card'><strong>Category radar</strong></div>", unsafe_allow_html=True)
            try:
                fig = get_category_radar_plotly(owned)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.error("Category radar not available.")
        
        with right:
            # Genres header
            st.markdown("<div class='card-header card'><strong>Genre playtime</strong></div>", unsafe_allow_html=True)
            try:
                fig = get_genre_donut_plotly(owned)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.error("Genre playtime not available.")

# --------------------------
# ACHIEVEMENTS Tab
# --------------------------
with tabs[2]:
    st.markdown("### Achievements — time patterns & milestones")
    if achievements.empty:
        st.markdown('<div class="card"><div class="story">No achievement data available. This can happen when achievements are private or the API call failed for some apps.</div></div>', unsafe_allow_html=True)
    else:
        a_col1, a_col2 = st.columns([0.5, 1])
        with a_col1:
            st.markdown('<div class="card"><strong>Achievement metrics</strong></div>', unsafe_allow_html=True)
            st.markdown(f"<div class='card'><div class='metric'>{num_achievements}</div><div class='metric-sub'>Total unlocked</div><div style='height:8px;'></div><div class='small-muted'>That's an average of <b>{round(num_achievements / max(1, num_games), 2)}</b> achievements per owned game.</div></div>", unsafe_allow_html=True)
            if peak_hour is not None:
                st.markdown(f"<div class='card small-muted'>Typical achievement hour: <b>{peak_hour}:00</b></div>", unsafe_allow_html=True)

        with a_col2:
            # Histogram: header only card, plot outside
            st.markdown("<div class='card-header card'><strong>When do you unlock achievements?</strong></div>", unsafe_allow_html=True)
            try:
                options = achievements.sort_values(by='unlocktime')['unlocktime'].dt.year.unique()
                options_list = ['All time']
                options_list.extend(list(options))
                selected = st.selectbox("Select year", options=options_list)
                if selected == "All time":
                    fig = get_achievement_hour_histogram_plotly(achievements)
                else:
                    fig = get_achievement_hour_histogram_plotly_by_year(achievements, selected)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.error("Could not build achievement histogram.")

            st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

        with st.container():
            col1, col2 = st.columns([0.5, 1])

            with col1:
                # Compute stats
                ach_by_game = achievements.groupby("appid").size().sort_values(ascending=False)
                top_appid = ach_by_game.index[0]
                top_count = ach_by_game.iloc[0]
                total_ach = len(achievements)
                share = round((top_count / total_ach) * 100, 1)

                # Fetch thumbnail from owned df
                try:
                    top_row = owned[owned["appid"] == top_appid].iloc[0]
                    img_url = top_row["image_path"]
                except Exception:
                    img_url = None

                # Display card with thumbnail + summary
                st.markdown("<div class='card'><strong>Achievement summary</strong></div>", unsafe_allow_html=True)

                # Thumbnail image
                if img_url:
                    st.markdown(
                        f"""
                        <div class='card' style='text-align:center; padding:10px;'>
                            <img src="{img_url}" style="width:240px; border-radius:8px;" />
                            <div style="margin-top:8px; font-weight:600;">{top_row['name']}</div>
                            <div class='small-muted'>{top_count} achievements</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        "<div class='card small-muted'>No thumbnail available.</div>",
                        unsafe_allow_html=True
                    )

                # Dynamic summary card
                st.markdown(
                    f"""
                    <div class='card' style='padding:12px;'>
                        <div class='small-muted'>
                            <b>{top_row['name']}</b> holds <b>{top_count}</b> of your achievements,
                            which is <b>{share}%</b> of all you've unlocked.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                # Achievement race (animated) — header + image OUTSIDE card
                st.markdown("<div class='card-header card'><strong>Achievement race (animated)</strong></div>", unsafe_allow_html=True)
                try:
                    gif_bytes = build_animated_bar_race(achievements, owned)
                    st.image(gif_bytes, use_container_width=True)
                    st.markdown("<div class='small-muted'>Animated ranking of achievement counts by game over time.</div>", unsafe_allow_html=True)
                except Exception:
                    st.error("Could not render achievement race.")

# --------------------------
# DEVELOPERS Tab
# --------------------------
with tabs[3]:
    st.markdown("### Developers — Where your games come from")
    with st.container():
        dev_col1, dev_col2 = st.columns([0.7, 0.3])
        with dev_col1:
            st.markdown("<div class='card-header card'><strong>Developer Origins (Map)</strong></div>", unsafe_allow_html=True)
            try:
                fig = get_developers_map_plotly(owned)
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.error("Developer map not available.")
        with dev_col2:
            st.markdown('<div class="card"><strong>Developer summary</strong>', unsafe_allow_html=True)
            if "developers" in owned.columns:
                top_devs = owned.explode('developers')['developers'].value_counts().head(5)
                st.markdown("<ul>" + "".join([f"<li class='small-muted'><b>{idx}</b>: {val} games</li>" for idx, val in top_devs.items()]) + "</ul>", unsafe_allow_html=True)
            else:
                st.markdown("<div class='small-muted'>No developer breakdown available in dataset.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# --------------------------
# ABOUT Tab
# --------------------------
with tabs[4]:
    st.markdown("### About this dashboard")
    st.markdown(
        """
        - Check your Steam profile's statistics! What kind of gamer are you? Which are your favorite game and genres? Find out!
        - This page uses publicly available information. You can change your Steam profile's privacy settings.
        - No affiliation with Valve nor any game developers or publishers.
        """
    )
    st.markdown("<div class='small-muted'>Built with ❤️.</div>", unsafe_allow_html=True)
