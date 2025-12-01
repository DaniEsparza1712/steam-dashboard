import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
import streamlit as st

steam_colors = [
    "#0E214D",
    "#09529A",
    "#1a9fff",
    "#66c0f4",
    "#ffb84c",
]

steam_cmap = LinearSegmentedColormap.from_list("steam_cmap", steam_colors)

@st.cache_data(show_spinner=True, show_time=True)
def get_achievement_hour_histogram_plotly(achievements):
    # Compute histogram
    counts, bins = np.histogram(achievements['hour'], bins=24, range=(0, 24))

    # Normalize counts → colormap
    norm = plt.Normalize(counts.min(), counts.max())
    colors = [f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {a})"
              for r, g, b, a in steam_cmap(norm(counts))]

    # X positions (0–23 as integers)
    x = bins[:-1]

    # Plotly bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x,
        y=counts,
        marker=dict(color=colors),
        text=counts,
        textposition="outside",
    ))

    # Layout styling
    fig.update_layout(
        title="Distribution of Achievement Unlock Times",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Achievements",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e4ddeb"),
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1,
            showgrid=False
        ),
        yaxis=dict(
            gridcolor="rgba(255,255,255,0.15)"
        ),
        margin=dict(l=40, r=10, t=50, b=40)
    )

    return fig

@st.cache_data(show_spinner=True, show_time=True)
def get_achievement_hour_histogram_plotly_by_year(achievements, year):
    hours_count = achievements.groupby('hour').agg({'achieved': 'count'})
    y_max = achievements.groupby('hour').agg({'achieved': 'count'})['achieved'].max()

    achievements = achievements[achievements['unlocktime'].dt.year == year]

    # Compute histogram
    counts, bins = np.histogram(achievements['hour'], bins=24, range=(0, 24))

    # Normalize counts → colormap
    norm = plt.Normalize(counts.min(), counts.max())
    colors = [f"rgba({int(r*255)}, {int(g*255)}, {int(b*255)}, {a})"
              for r, g, b, a in steam_cmap(norm(counts))]

    # X positions (0–23 as integers)
    x = bins[:-1]

    # Plotly bar chart
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=x,
        y=counts,
        marker=dict(color=colors),
        text=counts,
        textposition="outside",
    ))

    # Layout styling
    fig.update_layout(
        title="Distribution of Achievement Unlock Times",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Achievements",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e4ddeb"),
        xaxis=dict(
            tickmode="linear",
            tick0=0,
            dtick=1,
            showgrid=False
        ),
        yaxis=dict(
            range=[0, y_max],
            gridcolor="rgba(255,255,255,0.15)"
        ),
        margin=dict(l=40, r=10, t=50, b=40)
    )

    return fig
