__author__ = 'Greg'

import json
from operator import itemgetter
from datetime import datetime
# How to install pandas: https://gist.github.com/fyears/7601881
import pandas
import numpy
from sklearn import linear_model, cross_validation, datasets, preprocessing
import requests
from scipy.stats import binom


def turn_game_proba_into_series(number_of_games, number_of_games_to_win, team_proba, team_name):
    pmf = binom.pmf(number_of_games_to_win, number_of_games, team_proba)
    sf = binom.sf(number_of_games_to_win, number_of_games, team_proba)
    # take the pmf and add it to sf, so if it's a 5 game series take x=3 and add it to x > 3. To get what teams probability for winning 3 games is.
    proba = pmf + sf
    print('chance for {} to win series is: {}'.format(team_name, str(proba)))


def predict_on_model(logreg, real_array, team_name):
    print('logistical regression outcome for {} is: {}'.format(team_name, logreg.predict(real_array)))
    print('logistical regression probability is: {}'.format(logreg.predict_proba(real_array)))
    numpy_array = logreg.predict_proba(real_array)
    proba_list = numpy_array.tolist()[0]
    turn_game_proba_into_series(5, 3, proba_list[1], team_name)


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


def get_latest_team_stats_numpy_array(team_a, team_b, team_stats_df):
    # team_stats_df = team_stats_df[team_stats_df.team_id.isin([2, 1])]
    team_stats_df_a = team_stats_df[team_stats_df['team_id'] == team_a]
    team_stats_df_b = team_stats_df[team_stats_df['team_id'] == team_b]
    team_stats_df_a = team_stats_df_a.sort(['game_id'], ascending=False).head(1)
    team_stats_df_b = team_stats_df_b.sort(['game_id'], ascending=False).head(1)
    dict_team_a = team_stats_df_a.to_dict('records')[0]
    dict_team_b = team_stats_df_b.to_dict('records')[0]
    csum_prev_min_K_A = dict_team_a['csum_prev_min_K_A']
    # predictors = [dict_team_a['csum_prev_min_K_A'] - dict_team_b['csum_prev_min_K_A'],
    #               dict_team_a['csum_prev_min_minions_killed'] - dict_team_b['csum_prev_min_minions_killed'],
    #               dict_team_a['csum_prev_min_total_gold'] - dict_team_a['csum_prev_min_total_gold']]
    predictors = [dict_team_a['eff_K_A'] - dict_team_b['eff_K_A'],
                  dict_team_a['eff_minions_killed'] - dict_team_b['eff_minions_killed'],
                  dict_team_a['eff_total_gold'] - dict_team_a['eff_total_gold']]
    predictor_numpy_array = numpy.array([predictors])
    return predictor_numpy_array


def get_predictors_in_numpy_arrays(team_stats_df):
    games = get_predictors(team_stats_df)
    game_list = []
    y_array_list = []
    for game in games:
        if not (numpy.isnan(game['csum_prev_min_minions_killed']) and numpy.isnan(game['csum_prev_min_total_gold'])):
            # games_predictors = [game['csum_prev_min_K_A'], game['csum_prev_min_minions_killed'],
            #                     game['csum_prev_min_total_gold']]
            games_predictors = [game['eff_K_A'], game['eff_minions_killed'],
                                game['eff_total_gold']]
            game_list.append(games_predictors)
            y_array_list.append(game['y_element'])
    predictors = numpy.array(game_list)
    y_array = numpy.array([y_array_list])
    # print("predictors is: {}".format(predictors))
    # print("y array is: {}".format(y_array))
    return (predictors, y_array)


def get_team_stats_df(tuple_of_games):
    team_stats_df = get_team_stats_in_dataframe(tuple_of_games)
    team_stats_df = team_stats_df.sort(['game_id', 'team_id'])
    key_stats = ['game_number', 'game_length_minutes', 'kills', 'deaths', 'assists', 'minions_killed', 'total_gold',
                'K_A', 'A_over_K']
    team_stats_df['K_A'] = \
        team_stats_df['kills'] + team_stats_df['assists']
    team_stats_df['A_over_K'] = \
        team_stats_df['assists'] + team_stats_df['kills']
    team_grouped_by_game_id_df = team_stats_df.groupby(['game_id'], as_index=False).sum()
    team_stats_df = pandas.merge(team_stats_df, team_grouped_by_game_id_df, on=['game_id'])
    for key_stat in key_stats:
        # Need to add x/y to the keystat because when I add the groupby and merge the keystats get x and y added
        # to them at the end since they are the same name
        key_stat_x = '{}_x'.format(key_stat)
        key_stat_y = '{}_y'.format(key_stat)
        team_stats_df['csum_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id_x')[key_stat_x].cumsum()
        team_stats_df['csum_total_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id_x')[key_stat_y].cumsum()
        team_stats_df['csum_prev_{}'.format(key_stat)] = team_stats_df['csum_{}'.format(key_stat)] - team_stats_df[key_stat_x]
        team_stats_df['csum_total_prev_{}'.format(key_stat)] = \
            team_stats_df['csum_total_{}'.format(key_stat)] - team_stats_df[key_stat_y]
        team_stats_df['csum_prev_avg_{}'.format(key_stat)] = \
            team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_prev_game_number']
        team_stats_df['per_min_()'.format(key_stat)] = team_stats_df[key_stat_x] / team_stats_df['game_length_minutes_x']
        team_stats_df['csum_prev_percent_{}'.format(key_stat)] = \
            team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_total_prev_{}'.format(key_stat)]
        team_stats_df['margin_{}'.format(key_stat)] = \
            team_stats_df['csum_prev_percent_{}'.format(key_stat)] - (1 - team_stats_df['csum_prev_percent_{}'.format(key_stat)])
        team_stats_df['eff_{}'.format(key_stat)] = \
            team_stats_df['csum_prev_percent_{}'.format(key_stat)] / (1 - team_stats_df['csum_prev_percent_{}'.format(key_stat)])
        if key_stat not in ['game_number', 'game_length_minutes']:
            team_stats_df['csum_min_{}'.format(key_stat)] = \
                team_stats_df['csum_{}'.format(key_stat)] / team_stats_df['csum_game_length_minutes']
            team_stats_df['csum_prev_min_{}'.format(key_stat)] = \
                team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_prev_game_length_minutes']


    team_stats_df['csum_prev_kda'] = team_stats_df['csum_prev_kills'] * team_stats_df['csum_prev_assists']\
                                     / team_stats_df['csum_prev_deaths']
    team_stats_df = team_stats_df.sort(['game_id'])
    print(team_stats_df)
    return team_stats_df


def get_predictors(team_stats_df):
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
        key_stats = ['kills', 'deaths', 'assists', 'minions_killed', 'total_gold',
                'K_A', 'A_over_K']
        game_stat_predictor_dict = {}
        for key_stat in key_stats:
            game_stat_predictor_dict['csum_prev_min_{}'.format(key_stat)] = red_team['csum_prev_min_{}'.
                format(key_stat)] - blue_team['csum_prev_min_{}'.format(key_stat)]
        game_stat_predictor_dict['csum_prev_kda'] = red_team['csum_prev_kda'] - blue_team['csum_prev_kda']
        game_stat_predictor_dict['game_id'] = red_team['game_id']
        if red_team['won_x']:
            game_stat_predictor_dict['y_element'] = 1
        elif blue_team['won_x']:
            game_stat_predictor_dict['y_element'] = 0
        game_stats_predictors.append(game_stat_predictor_dict)
    return game_stats_predictors


def get_team_stats_in_dataframe(tuple_of_games):
    list_of_games = []
    team_stats_df = None
    x = 0
    for begin_game_id, end_game_id in tuple_of_games:
        for game_id in range(begin_game_id, end_game_id):
            response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
            game_league = response.text
            game = json.loads(game_league)
            blue_team_id = game['contestants']['blue']['id']
            red_team_id = game['contestants']['red']['id']
            winner_id = game['winnerId']
            if game != ['Entity not found']:
                blue_team, red_team = convert_league_stats_to_team_stats(game, winner_id, blue_team_id, red_team_id, game_id)
                blue_team_df = pandas.DataFrame(blue_team, index=[x])
                red_team_df = pandas.DataFrame(red_team, index=[x + 1])
                x += 2
                if team_stats_df is None:
                    team_stats_df = blue_team_df.append(red_team_df)
                else:
                    team_stats_df = team_stats_df.append(blue_team_df.append(red_team_df))
    # print(team_stats_df)
    return team_stats_df


def convert_league_stats_to_team_stats(game, winner_id, blue_team_id, red_team_id, game_id):
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
    blue_team['game_id'] = game_id
    red_team['game_id'] = game_id
    blue_team['team_id'] = int(blue_team_id)
    red_team['team_id'] = int(red_team_id)
    blue_team['game_length_minutes'] = game['gameLength']/60
    red_team['game_length_minutes'] = game['gameLength']/60
    blue_team['color'] = 'blue'
    red_team['color'] = 'red'
    blue_team['game_number'] = 1
    red_team['game_number'] = 1
    blue_team['team_name'] = game['contestants']['blue']['name']
    red_team['team_name'] = game['contestants']['red']['name']
    if winner_id == str(blue_team['team_id']):
        blue_team['won'] = True
        red_team['won'] = False
    elif winner_id == str(red_team['team_id']):
        blue_team['won'] = False
        red_team['won'] = True
    else:
        raise Exception("This is no winning team please check data!")
    return blue_team, red_team


def main():
    # NA and EU LCS
    # 6164, 6253
    # 6074, 6163
    eu_team_df = get_team_stats_df(((6074, 6163), (7061, 7065)))
    # na_team_df = get_team_stats_df(((6164, 6253), (7067, 7071)))
    eu_predictors, eu_y_array = get_predictors_in_numpy_arrays(eu_team_df)
    # na_predictors, na_y_array = get_predictors_in_numpy_arrays(na_team_df)
    # # Need to use concatenate for the predictors because we need an array of an arrays with predictors in each array
    # predictors = numpy.concatenate((eu_predictors, na_predictors))
    # # need to use append because we need an array of 0 and 1's
    # y_array = numpy.append(eu_y_array, na_y_array)
    # logreg = train_model(predictors, y_array)
    # lolgreg_standard, scaler = train_model_standard_scaler(predictors, y_array)
    # test_model(predictors, y_array)
    # # CLG vs TSM
    # real_array = get_latest_team_stats_numpy_array(2, 1, na_team_df)
    # predict_on_model(logreg, real_array, 'CLG')
    # # Fnatic vs Origen
    # real_array = get_latest_team_stats_numpy_array(68, 3862, eu_team_df)
    # predict_on_model(logreg, real_array, 'Fnatic')
if __name__ == "__main__":
    main()