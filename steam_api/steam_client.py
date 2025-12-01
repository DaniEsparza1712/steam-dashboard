import requests
import pandas as pd
import os
import streamlit as st

STEAM_API_KEY = st.secrets["STEAM_API_KEY"]

BASE = "https://api.steampowered.com"

#OWNED GAMES
def get_owned_games(account_id):
    owned_games_url = f'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key={STEAM_API_KEY}&steamid={account_id}&include_played_free_games=1&include_free_sub=1&format=json'
    response = requests.get(owned_games_url)
    data = response.json()
    owned_df = pd.DataFrame(data['response']['games'])
    owned_df['appid'] = owned_df['appid'].astype(str)
    return owned_df

def get_top_played_games(account_id):
    owned = get_owned_games(account_id)
    return owned.sort_values(by='playtime_forever', ascending=False)[:10]

def get_app_details(app_id):
    app_url = f'https://store.steampowered.com/api/appdetails?appids={app_id}&cc=mx'
    app_response = requests.get(app_url).json()
    entry = app_response.get(str(app_id), {})

    # If success is false or "data" missing → return safe defaults
    if not entry.get("success") or "data" not in entry:
        return {
            'appid': app_id,
            'name': 'None',
            'genres': None,
            'categories': None,
            'release_date': None,
            'image_path': None,
            'capsule_image_path': 'None',
            'required_age': None,
            'price': None,
            'developers':None
        }

    info = entry["data"]

    return {
        'appid': app_id,
        'name': info.get('name'),
        'genres': [g["description"] for g in info.get("genres", [])] if info.get("genres") else None,
        'categories': [c["description"] for c in info.get("categories", [])] if info.get("categories") else None,
        'release_date': info.get("release_date", {}).get("date"),
        'image_path': info.get("screenshots", [{}])[0].get("path_full") if info.get("screenshots") else None,
        'capsule_image_path': info.get('capsule_image'),
        'required_age': info.get('required_age'),
        'price': info.get('price_overview')['initial'] / 100 if info.get('price_overview') else None,
        'developers': info.get('developers')
    }

def get_top_played_df(account_id):
    top_played_df = get_top_played_games(account_id)[['appid', 'playtime_forever']]
    records = [get_app_details(id) for id in top_played_df['appid']]
    return pd.DataFrame(records).merge(top_played_df, how='left', on='appid')

def get_owned_df(account_id):
    owned_df = get_owned_games(account_id)[['appid', 'playtime_forever']]
    records = [get_app_details(id) for id in owned_df['appid']]
    owned = pd.DataFrame(records).merge(owned_df, how='left', on='appid')
    owned.drop(owned[owned['name']=='None'].index, inplace=True)
    return owned 

#USER DATA
def get_user_data(account_id):
    account_url = f'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={STEAM_API_KEY}&steamids={account_id}'
    account_response = requests.get(account_url)
    account_data = account_response.json()
    return account_data.get('response').get('players')[0]

def get_unlocked_achievements(app_id, account_id):
    url = (
        f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/"
        f"?appid={app_id}&key={STEAM_API_KEY}&steamid={account_id}"
    )

    response = requests.get(url)
    data = response.json().get("playerstats", {})

    # If game has no achievements, API returns: { "playerstats": { "success": false, "error": ... } }
    if not data.get("success", True):
        return pd.DataFrame(columns=[
            "apiname", "achieved", "unlocktime", "appid", "gameName"
        ])

    # If achievements key is missing
    achievements = data.get("achievements")
    if achievements is None:
        return pd.DataFrame(columns=[
            "apiname", "achieved", "unlocktime", "appid", "gameName"
        ])

    # Construct DataFrame
    df = pd.DataFrame(achievements)

    # Filter only unlocked
    df = df[df.get("achieved", 0) == 1]

    # Add game metadata
    df["appid"] = app_id
    df["gameName"] = data.get("gameName")

    # Convert unlock times
    if "unlocktime" in df.columns:
        df["unlocktime"] = (
            pd.to_datetime(df["unlocktime"], unit="s", utc=True)
              .dt.tz_convert("America/Mexico_City")
        )

    return df

