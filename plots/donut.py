
import plotly.graph_objects as go

text_color="#e4ddeb"
steam_palette = [
    "#66c0f4",  # light accent blue
    "#1f5baa",  # dark accent blue
    "#4c3f91",  # muted purple
    "#5d4b86",  # deep purple
    "#3b3054",  # dark violet
    "#1b2838",  # steam dark blue
    "#2a475e",  # mid blue
    "#171a21",  # almost-black blue
]

def get_genre_donut_plotly(owned):

    owned_genres = owned.explode('genres')
    owned_genres
    genre_playtime = owned_genres.groupby('genres')['playtime_forever'].sum().sort_values(ascending=True).reset_index(name='total_playtime')

    total_playtime = owned['playtime_forever'].sum()
    percentages = [f'{(playtime * 100 / total_playtime):.2f}%' for playtime in genre_playtime['total_playtime']]
    genre_playtime['percentages'] = percentages
    genre_playtime

    tailN = 7

    pie_genres = genre_playtime.tail(tailN)
    other_playtime = genre_playtime.iloc[:-tailN]['total_playtime'].sum()
    pie_genres.loc[len(pie_genres)] = ['Other', other_playtime, f'{(other_playtime * 100 / total_playtime):.2f}%']
    pie_genres

    values = pie_genres["total_playtime"]
    labels = pie_genres["genres"]
    colors = steam_palette[:len(values)]

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker=dict(
            colors=colors,
            line=dict(color="#03031A", width=0.5)
        ),
        textinfo="label+percent",
        textfont=dict(color=text_color, size=14),
        hovertemplate="<b>%{label}</b><br>%{percent:.1%}<extra></extra>",
    ))

    # Center text using annotation
    fig.update_layout(
        annotations=[
            dict(
                text=f"{total_playtime/60:.0f} hrs",
                x=0.5, y=0.5,
                font=dict(size=22, color=text_color),
                showarrow=False
            )
        ],
        title=dict(
            text="Playtime distribution by Genre",
            x=0.5,
            xanchor="center",
            font=dict(size=20, color=text_color)
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=80, b=30, l=30, r=30),
    )

    return fig
