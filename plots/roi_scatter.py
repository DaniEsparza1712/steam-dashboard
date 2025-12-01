import plotly.express as px
import plotly.graph_objects as go
from matplotlib.colors import LinearSegmentedColormap

text_color="#e4ddeb"
steam_colors = [
    "#0E214D",
    "#09529A",
    "#1a9fff",
    "#66c0f4",
    "#ffb84c",
]

steam_cmap = LinearSegmentedColormap.from_list("steam_cmap", steam_colors)
steam_colorscale = [
    (i / (len(steam_colors) - 1), color)
    for i, color in enumerate(steam_colors)
]

def get_roi_scatter_plot_plotly(owned):
    roi_df = owned.copy()
    prices_df = roi_df[['appid', 'name', 'price', 'playtime_forever']]
    prices_df['playtime_hours'] = prices_df['playtime_forever'] / 60.0
    prices_df = prices_df[prices_df['price'].notna()]
    prices_df['ROI'] = prices_df['playtime_hours'] * 10 / prices_df['price']
    
    median_roi = prices_df["ROI"].median()

    # Base scatter
    fig = px.scatter(
        prices_df,
        x="price",
        y="ROI",
        color="playtime_hours",
        size="playtime_hours",
        color_continuous_scale=steam_colorscale,
        hover_data=["name"] if "name" in prices_df.columns else None,
        labels={
            "price": "Price",
            "ROI": "Return on Investment",
            "playtime_hours": "Playtime (Hrs)"
        }
    )

    # Median ROI reference line
    fig.add_hline(
        y=median_roi,
        line_width=1.5,
        line_color="red",
        opacity=0.8
    )

    # Median label
    fig.add_annotation(
        x=min(prices_df["price"]),
        y=median_roi,
        text=f"{median_roi:.2f}",
        showarrow=False,
        font=dict(color=text_color, size=12),
        bgcolor="rgba(0,0,0,0.5)"
    )

    # Layout styling
    fig.update_layout(
        title=dict(
            text="<b>Return of Investment vs Price</b>",
            font=dict(color=text_color, size=22),
            x=0.5
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color=text_color),
        coloraxis_colorbar=dict(
            title="Playtime (Hrs)",
            tickcolor=text_color,
            tickfont=dict(color=text_color)
        )
    )

    # Axes styling
    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.2)",
        zeroline=False,
        color=text_color
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(255,255,255,0.2)",
        zeroline=False,
        color=text_color
    )

    return fig
