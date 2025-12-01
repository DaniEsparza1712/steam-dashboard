import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
from PIL import Image
import requests
from matplotlib.colors import to_hex
from matplotlib.animation import PillowWriter
import tempfile
import os

steam_colors = [
    "#ffb84c",
    "#66c0f4",
    "#1a9fff",
    "#09529A",
    "#0E214D"
]

steam_cmap = LinearSegmentedColormap.from_list("steam_cmap", steam_colors)

@st.cache_resource(show_spinner=True, show_time=True)
def build_animated_bar_race(achievements, owned, topN=15, interpolation_value=10):

    achievements['date'] = achievements['unlocktime'].dt.date
    counts = achievements.groupby(['date', 'appid']).size().reset_index(name='ach_count')
    dates = counts['date'].unique()
    games = []

    for game, gdf in counts.groupby('appid'):
        gdf = gdf.set_index('date').reindex(dates, fill_value=0)
        gdf['appid'] = game
        gdf['ach_count'] = gdf['ach_count'].astype(int)
        gdf['cumulative'] = gdf['ach_count'].cumsum()
        games.append(gdf)

    fixed = pd.concat(games)
    pivot = fixed.pivot(columns='appid', values='cumulative')

    appid_to_color = {
        appid: to_hex(steam_cmap(i / len(owned))) for i, appid in enumerate(owned['appid'].unique())
    }

    # ----- INTERPOLATION -----
    values = pivot[::5].values
    col_values = pivot[::5].columns.values
    dates_idx = pivot[::5].index.values
    real_frames = len(values)

    interp_frames, interp_dates = [], []
    for i in range(real_frames - 1):
        start, end = values[i], values[i + 1]
        for step in np.linspace(0, 1, interpolation_value, endpoint=False):
            interp_dates.append(dates_idx[i])
            interp_frames.append(start * (1 - step) + end * step)

    interp_dates.append(dates_idx[-1])
    interp_frames.append(values[-1])

    # ----- RANKS -----
    rank_frames = []

    for i in range(real_frames - 1):
        start_vals = pd.Series(values[i], index=col_values)
        end_vals = pd.Series(values[i + 1], index=col_values)

        start_top = start_vals.sort_values().tail(topN)
        end_top = end_vals.sort_values().tail(topN)

        union = list(set(start_top.index).union(end_top.index))

        start_r = start_vals[union].rank(method="first")
        end_r = end_vals[union].rank(method="first")

        for step in np.linspace(0, 1, interpolation_value, endpoint=False):
            rank_frames.append(start_r * (1 - step) + end_r * step)

    last_series = pd.Series(values[-1], index=col_values).sort_values().tail(topN)
    last_ranks = last_series.rank(method="first")
    rank_frames.append(last_ranks)

    # ----- ANIMATION -----
    fig = plt.figure(figsize=(8, 4), facecolor="#353437")
    rb_ax = fig.add_subplot(facecolor="#353437")
    text_color = "#e4ddeb"

    image_cache = {}
    def load_remote_image(url):
        if url not in image_cache:
            resp = requests.get(url)
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            image_cache[url] = np.array(img)
        return image_cache[url]

    def animate(i):
        rb_ax.clear()
        date = interp_dates[i]
        vals = pd.Series(interp_frames[i], index=col_values)
        ranks = rank_frames[i]

        row = vals.sort_values().tail(topN)
        apps = row.index
        vals_ord = row.values
        y_pos = ranks[apps].values
        colors = [appid_to_color[a] for a in apps]

        for y, v, c in zip(y_pos, vals_ord, colors):
            rb_ax.barh(y, v, color=c, height=0.8)

        for y, appid, v in zip(y_pos, apps, vals_ord):
            name = owned.loc[owned["appid"] == appid, "name"].values[0]
            rb_ax.text(v + 1, y, f"{name} ({v:.0f})", va="center", color=text_color)

        for y, appid in zip(y_pos, apps):
            url = owned.loc[owned["appid"] == appid, "capsule_image_path"].values[0]
            img = load_remote_image(url)
            oi = OffsetImage(img, zoom=0.15)
            ab = AnnotationBbox(oi, (0, y), xybox=(-40, 0), xycoords="data",
                                boxcoords="offset points", frameon=False)
            rb_ax.add_artist(ab)

        rb_ax.set_yticks([])
        rb_ax.set_xticks(np.arange(0, pivot.values.max() + 10, 10))
        rb_ax.tick_params(axis="x", colors=text_color)
        rb_ax.set_title(f"Achievements Unlocked: {date}", color=text_color)
        rb_ax.grid(axis="x", linestyle="--", alpha=0.4, color=text_color)

    anim = animation.FuncAnimation(fig, animate, frames=len(interp_frames), interval=45)

    # ==================================
    #  EXPORT GIF SAFELY (Windows-proof)
    # ==================================

    with tempfile.NamedTemporaryFile(delete=False, suffix=".gif") as tmp:
        temp_path = tmp.name

    anim.save(temp_path, writer=PillowWriter(fps=20))
    plt.close(fig)

    with open(temp_path, "rb") as f:
        gif_bytes = f.read()

    os.remove(temp_path)

    return gif_bytes
