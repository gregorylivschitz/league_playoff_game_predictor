import math

__author__ = 'Greg'

import json
from operator import itemgetter
from datetime import datetime
# How to install pandas: https://gist.github.com/fyears/7601881
import pandas
import numpy
from sklearn import linear_model, cross_validation, datasets, preprocessing
import requests


def predict_on_model(logreg):
    # CLG vs TIP
    real_array = numpy.array([[-0.341912, -9.095588, -4.566176, 14.077206, 456.878676, -44.019292]])
    print('logistical regression outcome is: {}'.format(logreg.predict(real_array)))
    print('logistical regression probability is: {}'.format(logreg.predict_proba(real_array)))

def test_model(test_predictors, test_y_array):
    logreg = linear_model.LogisticRegression()
    scores = cross_validation.cross_val_score(logreg, test_predictors, test_y_array, cv=5)
    print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

def train_model(predictors, y_array):
    logreg = linear_model.LogisticRegression()
    y_1darray = numpy.squeeze(y_array)
    logreg.fit(predictors, y_1darray)
    print('the predictors are {}'.format(predictors))
    print('the y_array is {}'.format(y_array))
    print('the coefficients are {}'.format(logreg.coef_))
    return logreg

def train_model_standard_scaler(predictors, y_array):
    scale = preprocessing.StandardScaler()
    scale.fit(predictors)
    predictors_standard_scaler = scale.transform(predictors)
    logreg = linear_model.LogisticRegression()
    logreg.fit(predictors, y_array)
    print('the standard scaler predictors are {}'.format(predictors_standard_scaler))
    print('the standard scaler y_array is {}'.format(y_array))
    print('the standard scaler coefficients are {}'.format(logreg.coef_))
    return (logreg, scale)



def get_predictors_in_numpy_arrays(begin_game, end_game, tournament_id):
    # games_eu = get_predictors(begin_game, end_game, tournament_id)
    # games_na = get_predictors(begin_game, end_game, tournament_id)
    # regions = [('na', games_na), ('eu', games_eu)]
    games = get_predictors(begin_game, end_game, tournament_id)
    game_list = []
    y_array_list = []
    for game in games:
        if not (numpy.isnan(game['csum_prev_avg_total_gold']) and numpy.isnan(game['csum_prev_avg_minions_killed'])):
            games_predictors = [game['csum_prev_avg_kills'], game['csum_prev_avg_deaths'], game['csum_prev_avg_assists'],
                                game['csum_prev_avg_minions_killed'], game['csum_prev_avg_total_gold'], game['csum_prev_gpm']]
            game_list.append(games_predictors)
            y_array_list.append(game['y_element'])
    predictors = numpy.array(game_list)
    y_array = numpy.array([y_array_list])
    # print("predictors is: {}".format(predictors))
    # print("y array is: {}".format(y_array))
    return (predictors, y_array)


def get_predictors(begin_game, end_game, tournament_id):
    team_stats_df = get_team_stats_in_dataframe(begin_game, end_game, tournament_id)
    team_stats_df = team_stats_df.sort(['game_id', 'team_id'])
    key_stats = ['game_number', 'kills', 'deaths', 'assists', 'minions_killed', 'total_gold', 'game_length_minutes']
    for key_stat in key_stats:
        team_stats_df['csum_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id')[key_stat].cumsum()
        team_stats_df['csum_prev_{}'.format(key_stat)] = team_stats_df['csum_{}'.format(key_stat)] - team_stats_df[key_stat]
        team_stats_df['csum_prev_avg_{}'.format(key_stat)] = \
            team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_prev_game_number']
    team_stats_df['gpm'] = team_stats_df['total_gold'] / team_stats_df['game_length_minutes']
    team_stats_df['csum_gpm'] = team_stats_df['csum_total_gold'] / team_stats_df['csum_game_length_minutes']
    team_stats_df['csum_prev_gpm'] = team_stats_df['csum_prev_total_gold'] / team_stats_df['csum_prev_game_length_minutes']
    team_stats_df = team_stats_df.sort(['game_id'])
    audit_team_stats_df = team_stats_df[['game_id', 'team_id', 'csum_prev_avg_kills', 'csum_prev_avg_deaths',
                                         'csum_prev_avg_assists', 'csum_prev_avg_minions_killed',
                                         'csum_prev_avg_total_gold', 'csum_prev_gpm']]

    #print(audit_team_stats_df[audit_team_stats_df['team_id'] == 2])
    # print(audit_team_stats_df[audit_team_stats_df.team_id.isin([2, 3657])])
    team_records = team_stats_df.to_dict('records')
    game_stats_predictors = []
    for team_index in range(0, len(team_records), 2):
        if team_records[team_index]['color'] == 'blue' and team_records[team_index + 1]['color'] == 'red':
            blue_team = team_records[team_index]
            red_team = team_records[team_index + 1]
        elif team_records[team_index]['color'] == 'red' and team_records[team_index + 1]['color'] == 'blue':
            red_team = team_records[team_index]
            blue_team = team_records[team_index + 1]
        else:
            raise Exception("Need both a blue and a red team in the game")
        if blue_team['game_id'] != red_team['game_id']:
            raise Exception('Huge problem game_id''s for teams did not match winnging_team game_id: {} '
                            'losing_team game_id: {}'.format(blue_team, red_team))
        key_stats = ['kills', 'deaths', 'assists', 'minions_killed', 'total_gold']
        game_stat_predictor_dict = {}
        for key_stat in key_stats:
            game_stat_predictor_dict['csum_prev_avg_{}'.format(key_stat)] = red_team['csum_prev_avg_{}'.
                format(key_stat)] - blue_team['csum_prev_avg_{}'.format(key_stat)]
        game_stat_predictor_dict['csum_prev_gpm'] = red_team['csum_prev_gpm'] - blue_team['csum_prev_gpm']
        game_stat_predictor_dict['game_id'] = red_team['game_id']
        if red_team['won']:
            game_stat_predictor_dict['y_element'] = 1
        elif blue_team['won']:
            game_stat_predictor_dict['y_element'] = 0
        game_stats_predictors.append(game_stat_predictor_dict)
    return game_stats_predictors


def get_team_stats_in_dataframe(begin_game, end_game, tournament_id):
    list_of_games = []
    team_stats_df = None
    for game_id in range(begin_game, end_game):
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        j_game_league = json.loads(game_league)
        j_game_league['dateTime'] = datetime.strptime(j_game_league['dateTime'], '%Y-%m-%dT%H:%MZ')
        j_game_league['game_id'] = game_id
        list_of_games.append(j_game_league)
    sorted_list_of_games = sorted(list_of_games, key=itemgetter('dateTime'))
    x = 0
    for game in sorted_list_of_games:
        blue_team_id = game['contestants']['blue']['id']
        red_team_id = game['contestants']['red']['id']
        winner_id = game['winnerId']
        if game != ['Entity not found'] and game['tournament']['id'] == tournament_id:
            blue_team, red_team = convert_league_stats_to_team_stats(game, winner_id, blue_team_id, red_team_id)
            blue_team_df = pandas.DataFrame(blue_team, index=[x])
            red_team_df = pandas.DataFrame(red_team, index=[x + 1])
            x += 2
            if team_stats_df is None:
                team_stats_df = blue_team_df.append(red_team_df)
            else:
                team_stats_df = team_stats_df.append(blue_team_df.append(red_team_df))
    # print(team_stats_df)
    return team_stats_df

def convert_league_stats_to_team_stats(game, winner_id, blue_team_id, red_team_id):
    blue_team = {}
    red_team = {}
    min_played = game['gameLength']/60
    blue_team_count = 0
    red_team_count = 0
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
        if int(blue_team_id) == team_id_of_player:
            blue_team_count += 1
            for key_stat, value_stat in key_stats.items():
                # pythonic way to do dictionary get a dictionary with a default value
                # if it doesn't exist assign 1 if it does add 1.
                blue_team[key_stat] = blue_team.setdefault(key_stat, 0) + value_stat
        elif int(red_team_id) == team_id_of_player:
            red_team_count += 1
            for key_stat, value_stat in key_stats.items():
                red_team[key_stat] = red_team.get(key_stat, 0) + value_stat
    blue_team['game_id'] = game['game_id']
    red_team['game_id'] = game['game_id']
    blue_team['team_id'] = int(blue_team_id)
    red_team['team_id'] = int(red_team_id)
    blue_team['game_length_minutes'] = game['gameLength']/60
    red_team['game_length_minutes'] = game['gameLength']/60
    blue_team['color'] = 'blue'
    red_team['color'] = 'red'
    blue_team['game_number'] = 1
    red_team['game_number'] = 1
    if winner_id == blue_team_id:
        blue_team['won'] = True
        red_team['won'] = False
    elif winner_id == red_team_id:
        blue_team['won'] = False
        red_team['won'] = True
    else:
        raise Exception("This is no winning team please check data!")
    return blue_team, red_team


def main():
    # NA and EU LCS
    # 6164, 6253
    # 6074, 6163
    eu_predictors, eu_y_array = get_predictors_in_numpy_arrays(6074, 6163, '225')
    na_predictors, na_y_array = get_predictors_in_numpy_arrays(6164, 6253, '226')
    # Need to use concatenate for the predictors because we need an array of an arrays with predictors in each array
    predictors = numpy.concatenate((eu_predictors, na_predictors))
    # need to use append because we need an array of 0 and 1's
    y_array = numpy.append(eu_y_array, na_y_array)
    logreg = train_model(predictors, y_array)
    test_model(predictors, y_array)
    predict_on_model(logreg)
if __name__ == "__main__":
    main()