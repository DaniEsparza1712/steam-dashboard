import matplotlib.pyplot as plt
import geopandas as gpd
import streamlit as st
from matplotlib.colors import LinearSegmentedColormap
import json
import pandas as pd
import plotly.express as px

with open("plots/countries.json") as f:
    data = json.load(f)

def get_dev_country(dev):
    match = dev_countries.loc[dev_countries['developer'] == dev, 'country']
    return match.iloc[0] if not match.empty else 'Unknown'
    
def get_count(country, count_df):
    match = count_df.loc[count_df['country'] == country, 'count']
    return match.iloc[0] if not match.empty else 0

dev_countries = pd.DataFrame([
    {"developer": dev, "country": country}
    for dev, country in data.items()
])


steam_colors = [
    "#0E214D",
    "#09529A",
    "#1a9fff",
    "#66c0f4",
    "#ffb84c",
]

steam_cmap = LinearSegmentedColormap.from_list("steam_cmap", steam_colors)

def get_developers_map(owned, text_color="#e4ddeb"):

    owned_devs = owned.explode(column='developers').groupby('developers').agg({'appid': 'count'})
    owned_devs.rename(columns={'appid': 'count'}, inplace=True)
    owned_devs.reset_index(inplace=True)

    owned_devs['country'] = [get_dev_country(dev) for dev in owned_devs['developers']]
    owned_devs.sort_values(by='country')

    country_count = owned_devs.groupby('country').agg({'count': 'sum'})
    country_count.reset_index(inplace=True)
    country_count.drop(country_count[country_count['country'] == 'Unknown'].index, inplace=True)

    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)
    world
    world['count'] = [get_count(country, country_count) for country in world['SOVEREIGNT']]

    fig, m_ax = plt.subplots(figsize=(10, 5))

    # Background colors
    fig.patch.set_facecolor('#000000')
    fig.patch.set_alpha(0)
    m_ax.set_facecolor('#000000')
    m_ax.set_alpha(0)

    # Plot the map
    map_ax = world.plot(
        column="count",
        cmap=steam_cmap,
        ax=m_ax,
        legend=True,
        edgecolor=text_color,
        linewidth=0.1,
    )

    # --- Colorbar styling ---
    cbar_ax = map_ax.get_figure().axes[-1]
    cbar = cbar_ax.collections[0].colorbar
    cbar_ax.tick_params(colors=text_color)

    # Colorbar border
    for spine in cbar_ax.spines.values():
        spine.set_edgecolor(text_color)

    # Title
    map_ax.set_title(
        "Developers by Country for Owned Games",
        color=text_color,
        fontweight="bold"
    )

    # Hide ticks
    map_ax.set_xticks([])
    map_ax.set_yticks([])

    # Axes borders
    for pos in ["bottom", "top", "left", "right"]:
        map_ax.spines[pos].set_color(text_color)

    plt.tight_layout()
    return fig

def get_developers_map_plotly(owned, text_color="#e4ddeb"):

    # --- compute developer → country and country counts ---
    owned_devs = (
        owned.explode(column='developers')
             .groupby('developers')
             .agg({'appid': 'count'})
             .rename(columns={'appid': 'count'})
             .reset_index()
    )

    owned_devs['country'] = [get_dev_country(dev) for dev in owned_devs['developers']]

    country_count = (
        owned_devs.groupby('country')
                  .agg({'count': 'sum'})
                  .reset_index()
    )

    country_count = country_count[country_count["country"] != "Unknown"]

    # --- Load world geometry from geopandas ---
    url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
    world = gpd.read_file(url)

    # Merge with counts by country name ("SOVEREIGNT")
    world = world.merge(country_count, how="left", left_on="SOVEREIGNT", right_on="country")
    world["count"].fillna(0, inplace=True)

    # Convert geometry to GeoJSON
    world_json = world.__geo_interface__

    # Extract center for map positioning
    world["centroid_lon"] = world.geometry.centroid.x
    world["centroid_lat"] = world.geometry.centroid.y

    # --- Build Plotly Choropleth ---
    fig = px.choropleth_mapbox(
        world,
        geojson=world_json,
        locations=world.index,
        color="count",
        mapbox_style="carto-darkmatter",
        hover_name="SOVEREIGNT",
        color_continuous_scale=steam_colors,
        opacity=0.85,
        center={"lat": 20, "lon": 0},
        zoom=1,
    )

    # Layout styling
    fig.update_layout(
        title_text="Developers by Country for Owned Games",
        title_font=dict(color=text_color, size=22),
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    # Colorbar styling
    fig.update_coloraxes(
        colorbar=dict(
            title="Count",
            tickfont=dict(color=text_color),
        )
    )

    return fig