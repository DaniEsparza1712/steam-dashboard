import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from io import BytesIO
from PIL import Image
import requests
import base64
import math
import plotly.graph_objects as go
import streamlit as st
from matplotlib.colors import to_hex


steam_colors = [
    "#ffb84c",
    "#66c0f4",
    "#1a9fff",
    "#09529A",
    "#0E214D"
]

steam_cmap = LinearSegmentedColormap.from_list("steam_cmap", steam_colors)
bg_color = "#1b1f23"
text_color = "#e4ddeb"

image_cache = {}

def load_remote_image(url):
    if url not in image_cache:
        response = requests.get(url)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        image_cache[url] = np.array(img)
    return image_cache[url]


def encode_image(url):
    r = requests.get(url)
    return base64.b64encode(r.content).decode()

@st.cache_resource(show_spinner=True, show_time=True)
def get_top_games_plot_plotly(top):
    appid_to_color = {
        appid: to_hex(steam_cmap(i / len(top))) for i, appid in enumerate(top['appid'].unique())
    }

    top_df = top.sort_values(by="playtime_forever").copy()
    top_df["playtime_forever"] /= 60.0 

    # Plotly horizontal bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=top_df["playtime_forever"],
        y=top_df["name"],
        orientation="h",
        marker=dict(
            color=[appid_to_color[appid] for appid in top_df["appid"]]
        ),
        hoverinfo="skip" # no tooltips (images are overlays)
    ))

    # Add text labels at the right side of bars
    fig.update_traces(
        text=[
            f"{name} ({hours:.1f} hrs)"
            for name, hours in zip(top_df["name"], top_df["playtime_forever"])
        ],
        textposition="outside",
        textfont=dict(color=text_color, size=10)
    )

    # Add capsule images as overlay
    images = []
    for i, row in top_df.iterrows():

        if row["capsule_image_path"] and str(row["capsule_image_path"]) != "None":
            img_b64 = encode_image(row["capsule_image_path"])

            # Position: y is the index of the bar
            # xref='paper' means x relative to full figure (0 to 1)
            images.append(dict(
                source=f"data:image/png;base64,{img_b64}",
                xref="paper",
                yref="y",
                x=-0.005,         # to the left of bars
                y=row["name"],   # vertical alignment
                sizex=0.1,
                sizey=0.9,       # controls bar alignment
                xanchor="right",
                yanchor="middle",
                layer="below"
            ))

    fig.update_layout(images=images)

    # Layout styling
    fig.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=80, r=30, t=20, b=20),
        xaxis=dict(
            title="Hours Played",
            color=text_color,
            showgrid=False
        ),
        yaxis=dict(
            showticklabels=False,
            color=text_color,
            showgrid=False
        )
    )

    return fig


def get_top_games_plot(top):
    appid_to_color = {
        appid: steam_cmap(i / len(top)) for i, appid in enumerate(top['appid'].unique())
    }

    fig, ax = plt.subplots(figsize=(8, 3), facecolor=bg_color)
    ax.set_facecolor(bg_color)

    print(top['capsule_image_path'])

    top_df = top.sort_values(by='playtime_forever').copy()
    top_df['playtime_forever'] /= 60.0

    colors = [appid_to_color[appid] for appid in top_df['appid']]
    bars = ax.barh(top_df['name'], top_df['playtime_forever'], color=colors)

    # Add capsule images
    for appid, bar in zip(top_df['appid'], bars):
        img_url = top.loc[top['appid'] == appid, 'capsule_image_path'].values[0]
        y = bar.get_y() + bar.get_height() / 2
        if str(img_url) != 'None':
            img = load_remote_image(img_url)
            oi = OffsetImage(img, zoom=0.15)
            ab = AnnotationBbox(
                oi,
                (0, y),
                xybox=(-25, 0),
                xycoords='data',
                boxcoords='offset points',
                frameon=False
            )
            ax.add_artist(ab)

        ax.text(
            bar.get_width() + 1,
            y,
            f"{top_df.loc[top_df['appid'] == appid, 'name'].values[0]} "
            f"({top_df.loc[top_df['appid'] == appid, 'playtime_forever'].values[0]:.1f} hrs)",
            va='center',
            color=text_color,
            fontsize=6
        )

    # Style
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(text_color)
    ax.spines['left'].set_color(text_color)

    ax.set_yticks([]) 
    ax.tick_params(colors=text_color)

    plt.tight_layout()
    return fig
