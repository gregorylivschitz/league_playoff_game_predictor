__author__ = 'Greg'

import requests
import json
from team_stats import TeamStats


def get_team_stats():
    # 6164, 6253
    for game_id in range(6164, 6166):
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        j_game_league = json.loads(game_league)
        winning_team_id = j_game_league['winnerId']
        losing_team_id = None
        red_team = j_game_league['contestants']['red']
        blue_team = j_game_league['contestants']['blue']
        if red_team['id'] == winning_team_id:
            winning_team_name = red_team['name']
            losing_team_name = blue_team['name']
            losing_team_id = blue_team['id']
        else:
            losing_team_id = red_team['id']
            winning_team_name = blue_team['name']
            losing_team_name = red_team['name']
        if j_game_league != ['Entity not found'] and j_game_league['tournament']['id'] == '226':
            winning_team, losing_team = convert_league_stats_to_team_stats(j_game_league, winning_team_id, losing_team_id)
            print(winning_team)
            print(losing_team)


def convert_league_stats_to_team_stats(j_game_league, winning_team_id, losing_team_id):
    winning_team = {}
    losing_team = {}
    min_played = j_game_league['gameLength']/60
    winning_team_count = 0
    losing_team_count = 0
    for player_index in range(0, 10):
        j_player_stats = j_game_league['players']['player{}'.format(player_index)]
        team_id_of_player = j_player_stats['teamId']
        player_name = j_player_stats['name']
        kda = j_player_stats['kda']
        kills = j_player_stats['kills']
        deaths = j_player_stats['deaths']
        assits = j_player_stats['assists']
        minions_killed = j_player_stats['minionsKilled']
        total_gold = j_player_stats['totalGold']
        gpm = total_gold/min_played
        key_stats = {'kda': kda, 'kills': kills, 'deaths': deaths, 'assists': assits,
                     'minions_killed': minions_killed, 'total_gold': total_gold, 'gpm': gpm}
        if int(winning_team_id) == team_id_of_player:
            winning_team_count += 1
            for key_stat, value_stat in key_stats.items():
                # pythonic way to do dictionary get a dictionary with a default value
                # if it doesn't exist assign 1 if it does add 1.
                winning_team[key_stat] = winning_team.setdefault(key_stat, 0) + value_stat
        elif int(losing_team_id) == team_id_of_player:
            losing_team_count += 1
            for key_stat, value_stat in key_stats.items():
                losing_team[key_stat] = losing_team.get(key_stat, 0) + value_stat
    return winning_team, losing_team


def main():
    get_team_stats()

if __name__ == "__main__":
    main()