"""
Steam Games Data Fetcher and Processor

This module fetches data from the Steam API and processes it to generate a JSON file
and HTML pages to display the data.
"""

import json
import os
import requests
from tqdm import tqdm
from local_config import API_KEY, STEAM_ID

def get_owned_games(api_key, steam_id):
    """Fetch the list of games owned by the user."""
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        return response.json().get('response', {}).get('games', [])
    return []

def get_game_details(api_key, steam_id, appid):
    """Fetch detailed stats and achievements for a specific game."""
    user_stats_url = "http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/"
    global_achievements_url = (
        "http://api.steampowered.com/ISteamUserStats/"
        "GetGlobalAchievementPercentagesForApp/v2/"
    )
    player_achievements_url = (
        "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
    )

    user_stats_params = {
        "key": api_key,
        "steamid": steam_id,
        "appid": appid
    }
    global_achievements_params = {
        "gameid": appid
    }
    player_achievements_params = {
        "key": api_key,
        "steamid": steam_id,
        "appid": appid
    }

    user_stats_response = requests.get(user_stats_url, params=user_stats_params, timeout=10)
    global_achievements_response = requests.get(
        global_achievements_url, params=global_achievements_params, timeout=10
    )
    player_achievements_response = requests.get(
        player_achievements_url, params=player_achievements_params, timeout=10
    )

    user_stats = (
        user_stats_response.json().get('playerstats', {})
        if user_stats_response.status_code == 200 else {}
    )
    global_achievements = (
        global_achievements_response.json()
        .get('achievementpercentages', {})
        .get('achievements', [])
        if global_achievements_response.status_code == 200 else []
    )
    player_achievements = (
        player_achievements_response.json()
        .get('playerstats', {})
        .get('achievements', [])
        if player_achievements_response.status_code == 200 else []
    )

    return user_stats, global_achievements, player_achievements

def format_playtime(hours):
    """Format playtime in hours to a human-readable string."""
    days = int(hours // 24)
    hours = int(hours % 24)
    minutes = int((hours % 1) * 60)
    return f"{days}d {hours}h {minutes}m"

def generate_json(games, api_key, steam_id):
    """Generate a JSON file with game data and statistics."""
    total_hours = 0
    not_played_count = 0
    games_data = []

    for game in tqdm(games, desc="Processing games"):
        name = game.get('name', 'Unknown')
        playtime_hours = game.get('playtime_forever', 0) / 60  # converting minutes to hours
        total_hours += playtime_hours
        if playtime_hours == 0:
            not_played_count += 1

        user_stats, global_achievements, player_achievements = get_game_details(
            api_key, steam_id, game['appid']
        )

        game_data = {
            'name': name,
            'playtime_hours': playtime_hours,
            'appid': game['appid'],
            'user_stats': user_stats,
            'global_achievements': global_achievements,
            'player_achievements': player_achievements
        }

        games_data.append(game_data)

    summary = {
        'total_games': len(games),
        'total_hours': total_hours,
        'total_hours_formatted': format_playtime(total_hours),
        'not_played_count': not_played_count,
        'games': games_data
    }

    if not os.path.exists("WWW"):
        os.makedirs("WWW")

    with open(os.path.join("WWW", "steam_data.json"), "w", encoding='utf-8') as file:
        json.dump(summary, file, indent=4)

def main():
    """Main function to fetch game data and generate JSON."""
    games = get_owned_games(API_KEY, STEAM_ID)

    if not games:
        print("No games found or failed to retrieve data.")
        return

    generate_json(games, API_KEY, STEAM_ID)

if __name__ == "__main__":
    main()
