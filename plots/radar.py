import plotly.graph_objects as go
import numpy as np

text_color="#e4ddeb"

def get_category_radar_plotly(owned):

    cat_df = owned.explode('categories')
    cat_df.reset_index(inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Steam Achievements'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Full controller support'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Partial Controller Support'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Steam Trading Cards'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Family Sharing'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Remote Play on Tablet'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Remote Play on Phone'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Remote Play Together'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Remote Play on TV'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Steam Leaderboards'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Steam Cloud'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Custom Volume Controls'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Surround Sound'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Stereo Sound'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Camera Comfort'].index, inplace=True)
    cat_df.drop(cat_df[cat_df['categories'] == 'Captions available'].index, inplace=True)

    cat_play = cat_df.groupby('categories')['playtime_forever'].sum() / 60.0
    topN = 10
    cat_play = cat_play.sort_values(ascending=False).head(topN)

    labels = cat_play.index.tolist()
    values = cat_play.values.tolist()

    # Close the loop (radar charts require repeating first point)
    labels.append(labels[0])
    values.append(values[0])

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        mode='lines+markers',
        line=dict(width=2, dash='dash'),
        fill='toself',
        opacity=0.5
    ))

    fig.update_layout(
        title=dict(
            text="Category distribution by playtime",
            font=dict(size=18, color=text_color),
            y=0.95
        ),
        polar=dict(
            bgcolor="#1E2331",
            radialaxis=dict(showticklabels=False, showgrid=True, gridcolor="#636373"),
            angularaxis=dict(showgrid=True, gridcolor="#636373", tickfont=dict(color=text_color))
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=80, b=20),
        showlegend=False
    )

    return fig
