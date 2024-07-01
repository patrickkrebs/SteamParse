import requests
from local_config import API_KEY, STEAM_ID
from prettytable import PrettyTable
import os

def get_owned_games(api_key, steam_id):
    url = "http://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
    params = {
        "key": api_key,
        "steamid": steam_id,
        "include_appinfo": True,
        "include_played_free_games": True,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('response', {}).get('games', [])
    else:
        print(f"Failed to get data: {response.status_code}")
        return []

def get_game_details(api_key, steam_id, appid):
    user_stats_url = "http://api.steampowered.com/ISteamUserStats/GetUserStatsForGame/v2/"
    global_achievements_url = "http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2/"
    player_achievements_url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/"
    
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
    
    user_stats_response = requests.get(user_stats_url, params=user_stats_params)
    global_achievements_response = requests.get(global_achievements_url, params=global_achievements_params)
    player_achievements_response = requests.get(player_achievements_url, params=player_achievements_params)
    
    user_stats = user_stats_response.json().get('playerstats', {}) if user_stats_response.status_code == 200 else {}
    global_achievements = global_achievements_response.json().get('achievementpercentages', {}).get('achievements', []) if global_achievements_response.status_code == 200 else []
    player_achievements = player_achievements_response.json().get('playerstats', {}).get('achievements', []) if player_achievements_response.status_code == 200 else []
    
    return user_stats, global_achievements, player_achievements

def format_playtime(hours):
    days = int(hours // 24)
    hours = int(hours % 24)
    minutes = int((hours % 1) * 60)
    return f"{days}d {hours}h {minutes}m"

def display_games(games, sort_by):
    table = PrettyTable()
    table.field_names = ["Game", "Hours Played"]
    
    total_hours = 0
    not_played_count = 0
    games_data = []

    for game in games:
        name = game.get('name', 'Unknown')
        playtime_hours = game.get('playtime_forever', 0) / 60  # converting minutes to hours
        total_hours += playtime_hours
        if playtime_hours == 0:
            not_played_count += 1
        table.add_row([name, playtime_hours])
        games_data.append((name, playtime_hours, game.get('appid')))

    if sort_by == "alphabetical":
        games_data.sort(key=lambda x: x[0])
    elif sort_by == "time":
        games_data.sort(key=lambda x: x[1], reverse=True)

    table.float_format = ".2"  # Format the hours played to 2 decimal places
    
    print(table)
    print("\nTotal Games:", len(games))
    print("Total Hours Played:", f"{total_hours:.2f} ({format_playtime(total_hours)})")
    print("Games Not Played:", not_played_count)

    generate_html(games_data, len(games), total_hours, not_played_count)

def generate_html(games_data, total_games, total_hours, not_played_count):
    if not os.path.exists("WWW"):
        os.makedirs("WWW")

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Steam Games Summary</title>
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
            }
            th, td {
                border: 1px solid black;
                padding: 8px;
                text-align: left;
            }
            th {
                background-color: #f2f2f2;
            }
        </style>
    </head>
    <body>
        <h1>Steam Games Summary</h1>
        <table>
            <tr>
                <th>Game</th>
                <th>Hours Played</th>
            </tr>
    """

    for game, hours, appid in games_data:
        html_content += f"""
            <tr>
                <td><a href="game_{appid}.html">{game}</a></td>
                <td>{hours:.2f}</td>
            </tr>
        """
        generate_game_details_html(game, appid)

    html_content += f"""
        </table>
        <p>Total Games: {total_games}</p>
        <p>Total Hours Played: {total_hours:.2f} ({format_playtime(total_hours)})</p>
        <p>Games Not Played: {not_played_count}</p>
    </body>
    </html>
    """

    with open(os.path.join("WWW", "steam_games_summary.html"), "w") as file:
        file.write(html_content)

def generate_game_details_html(game_name, appid):
    user_stats, global_achievements, player_achievements = get_game_details(API_KEY, STEAM_ID, appid)
    
    user_stats_html = "<h2>User Stats</h2><ul>"
    for stat in user_stats.get('stats', []):
        user_stats_html += f"<li>{stat['name']}: {stat['value']}</li>"
    user_stats_html += "</ul>"

    global_achievements_html = "<h2>Global Achievements</h2><ul>"
    for achievement in global_achievements:
        global_achievements_html += f"<li>{achievement['name']}: {achievement['percent']}%</li>"
    global_achievements_html += "</ul>"

    player_achievements_html = "<h2>Player Achievements</h2><ul>"
    for achievement in player_achievements:
        player_achievements_html += f"<li>{achievement['apiname']}: {'Achieved' if achievement['achieved'] == 1 else 'Not Achieved'}</li>"
    player_achievements_html += "</ul>"

    game_details_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{game_name} Details</title>
    </head>
    <body>
        <h1>{game_name} Details</h1>
        {user_stats_html}
        {global_achievements_html}
        {player_achievements_html}
        <p><a href="steam_games_summary.html">Back to Summary</a></p>
    </body>
    </html>
    """

    with open(os.path.join("WWW", f"game_{appid}.html"), "w") as file:
        file.write(game_details_html)

def main():
    games = get_owned_games(API_KEY, STEAM_ID)
    
    if not games:
        print("No games found or failed to retrieve data.")
        return

    sort_by = "alphabetical"  # Default sort by alphabetical

    while True:
        display_games(games, sort_by)
        print("\nEnter 'alphabetical' to sort by game name or 'time' to sort by hours played.")
        print("Enter 'exit' to quit.")
        user_input = input("Sort by (alphabetical/time/exit): ").strip().lower()

        if user_input in ["alphabetical", "time"]:
            sort_by = user_input
        elif user_input == "exit":
            break
        else:
            print("Invalid option. Please enter 'alphabetical', 'time', or 'exit'.")

if __name__ == "__main__":
    main()