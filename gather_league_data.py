__author__ = 'Greg'

import json
from operator import itemgetter
from datetime import datetime
# How to install pandas: https://gist.github.com/fyears/7601881
import pandas
import numpy
import scipy
import requests

def set_up_data_frame():
    team_stats_df = get_team_stats_in_dataframe()
    #print(team_stats_df)
    print(team_stats_df.cumsum())
    team_stats_df.drop(team_stats_df.columns[[0, 1,  3, 4, 6, 8]], axis=1, inplace=True)
    team_stats_df = team_stats_df.sort(['team_id'])
    team_stats_df['csum_kills'] = team_stats_df.groupby(['team_id'])['kills'].cumsum()
    team_stats_df['csum_prev_kills'] = team_stats_df['csum_kills'] - team_stats_df['kills']
    team_stats_df = team_stats_df.sort(['game_id'])
    print(team_stats_df)




def get_team_stats_in_dataframe():
    list_of_games = []
    team_stats_df = None
    # 6164, 6253
    for game_id in range(6164, 6180):
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        j_game_league = json.loads(game_league)
        j_game_league['dateTime'] = datetime.strptime(j_game_league['dateTime'], '%Y-%m-%dT%H:%MZ')
        j_game_league['game_id'] = game_id
        list_of_games.append(j_game_league)
    sorted_list_of_games = sorted(list_of_games, key=itemgetter('dateTime'))
    for game in sorted_list_of_games:
        winning_team_id = game['winnerId']
        losing_team_id = None
        red_team = game['contestants']['red']
        blue_team = game['contestants']['blue']
        if red_team['id'] == winning_team_id:
            winning_team_name = red_team['name']
            losing_team_name = blue_team['name']
            losing_team_id = blue_team['id']
        else:
            losing_team_id = red_team['id']
            winning_team_name = blue_team['name']
            losing_team_name = red_team['name']
        if game != ['Entity not found'] and game['tournament']['id'] == '226':
            winning_team, losing_team = convert_league_stats_to_team_stats(game, winning_team_id, losing_team_id)
            winning_team_df = pandas.DataFrame(winning_team, index=[0])
            losing_team_df = pandas.DataFrame(losing_team, index=[0])
            if team_stats_df is None:
                team_stats_df = winning_team_df.append(losing_team_df)
            else:
                team_stats_df = team_stats_df.append(winning_team_df.append(losing_team_df))
    return team_stats_df

def convert_league_stats_to_team_stats(game, winning_team_id, losing_team_id):
    winning_team = {}
    losing_team = {}
    min_played = game['gameLength']/60
    winning_team_count = 0
    losing_team_count = 0
    for player_index in range(0, 10):
        j_player_stats = game['players']['player{}'.format(player_index)]
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
    winning_team['game_id'] = game['game_id']
    losing_team['game_id'] = game['game_id']
    winning_team['team_id'] = int(winning_team_id)
    losing_team['team_id'] = int(losing_team_id)
    return winning_team, losing_team


def main():
    set_up_data_frame()

if __name__ == "__main__":
    main()