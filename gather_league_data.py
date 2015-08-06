__author__ = 'Greg'

import json
from operator import itemgetter
from datetime import datetime
# How to install pandas: https://gist.github.com/fyears/7601881
import pandas
import numpy
from sklearn import linear_model, datasets
import requests


def train_and_predict():
    predictors = get_predictors()
    logreg = linear_model.LogisticRegression()
    key_stats = ['kills', 'deaths', 'assists', 'minions_killed', 'total_gold', 'gpm']

    for predictor in predictors:
        if predictor['csum_prev_total_gold'] != 0 and predictor['csum_prev_minions_killed'] != 0:
            predict_array = numpy.asarray([predictor['csum_prev_kills'], predictor['csum_prev_deaths'],
                        predictor['csum_prev_assists'], predictor['csum_prev_minions_killed'],
                        predictor['csum_prev_total_gold']])
            y_array = numpy.array([0, 1])
            logreg.fit(predict_array, y_array)
    real_array = numpy.array([[64, 39, 149, 19216, -45577]])
    print(logreg.predict(real_array))



def get_predictors():
    team_stats_df = get_team_stats_in_dataframe()
    #print(team_stats_df)
    #team_stats_df.drop(team_stats_df.columns[[0, 1,  3, 4, 6, 8]], axis=1, inplace=True)
    team_stats_df = team_stats_df.sort(['team_id'])
    key_stats = ['kills', 'deaths', 'assists', 'minions_killed', 'total_gold', 'game_length_minutes']
    for key_stat in key_stats:
        team_stats_df['csum_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id')[key_stat].cumsum()
        team_stats_df['csum_prev_{}'.format(key_stat)] = team_stats_df['csum_{}'.format(key_stat)] - team_stats_df[key_stat]
    team_stats_df['gpm'] = team_stats_df['total_gold'] / team_stats_df['game_length_minutes']
    team_stats_df['csum_gpm'] = team_stats_df['csum_total_gold'] / team_stats_df['csum_game_length_minutes']
    team_stats_df['csum_prev_gpm'] = team_stats_df['csum_prev_total_gold'] / team_stats_df['csum_prev_game_length_minutes']
    team_stats_df = team_stats_df.sort(['game_id'])
    team_records = team_stats_df.to_dict('records')
    # print(team_records)
    game_stats_predictors = []
    for team_index in range(0, len(team_records), 2):
        if team_records[team_index]['won']:
            winning_team = team_records[team_index]
            losing_team = team_records[team_index + 1]
        else:
            winning_team = team_records[team_index + 1]
            losing_team = team_records[team_index]
        if winning_team['game_id'] != losing_team['game_id']:
            raise Exception('Huge problem game_id''s for teams did not match winnging_team game_id: {} '
                            'losing_team game_id: {}'.format(winning_team, losing_team))
        key_stats = ['kills', 'deaths', 'assists', 'minions_killed', 'total_gold', 'gpm']
        game_stat_predictor_dict = {}
        for key_stat in key_stats:
            # print('winning team: ' + str(winning_team['csum_prev_{}'.format(key_stat)]))
            # print('losing team: ' + str(losing_team['csum_prev_{}'.format(key_stat)]))
            game_stat_predictor_dict['csum_prev_{}'.format(key_stat)] = winning_team['csum_prev_{}'.
                format(key_stat)] - losing_team['csum_prev_{}'.format(key_stat)]
            # print('subtracted: ' + str(game_stat_predictor_dict['csum_prev_{}'.format(key_stat)]))
        game_stat_predictor_dict['game_id'] = winning_team['game_id']
        game_stats_predictors.append(game_stat_predictor_dict)
    # print(game_stats_predictors)
    return game_stats_predictors


def get_team_stats_in_dataframe():
    list_of_games = []
    team_stats_df = None
    # 6164, 6253
    for game_id in range(6164, 6190):
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        j_game_league = json.loads(game_league)
        j_game_league['dateTime'] = datetime.strptime(j_game_league['dateTime'], '%Y-%m-%dT%H:%MZ')
        j_game_league['game_id'] = game_id
        list_of_games.append(j_game_league)
    sorted_list_of_games = sorted(list_of_games, key=itemgetter('dateTime'))
    x = 0
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
            winning_team_df = pandas.DataFrame(winning_team, index=[x])
            losing_team_df = pandas.DataFrame(losing_team, index=[x + 1])
            x += 2
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
        #kda = j_player_stats['kda']
        kills = j_player_stats['kills']
        deaths = j_player_stats['deaths']
        assits = j_player_stats['assists']
        minions_killed = j_player_stats['minionsKilled']
        total_gold = j_player_stats['totalGold']
        gpm = total_gold/min_played
        key_stats = {'kills': kills, 'deaths': deaths, 'assists': assits,
                     'minions_killed': minions_killed, 'total_gold': total_gold}
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
    winning_team['game_length_minutes'] = game['gameLength']/60
    losing_team['game_length_minutes'] = game['gameLength']/60
    winning_team['won'] = True
    losing_team['won'] = False
    return winning_team, losing_team


def main():
    train_and_predict()

if __name__ == "__main__":
    main()