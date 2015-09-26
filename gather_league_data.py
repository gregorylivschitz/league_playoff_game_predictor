import os
from threading import Thread

__author__ = 'Greg'

import json

# How to install pandas: https://gist.github.com/fyears/7601881
import pandas
import numpy
from sklearn import linear_model, cross_validation, datasets, preprocessing
import requests
from scipy.stats import binom
from sqlalchemy import create_engine

# def predict_winner_of_group(team_one, team_two, team_three, team_four):


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


def get_latest_team_stats_numpy_array(team_a, team_b, team_stats_df, predictor_stats):
    game_predictor_stats = []
    # team_stats_df = team_stats_df[team_stats_df.team_id.isin([2, 1])]
    team_stats_df_a = team_stats_df[team_stats_df['team_id_x'] == team_a]
    team_stats_df_b = team_stats_df[team_stats_df['team_id_x'] == team_b]
    team_stats_df_a = team_stats_df_a.sort(['game_id'], ascending=False).head(1)
    team_stats_df_b = team_stats_df_b.sort(['game_id'], ascending=False).head(1)
    dict_team_a = team_stats_df_a.to_dict('records')[0]
    dict_team_b = team_stats_df_b.to_dict('records')[0]
    # csum_prev_min_K_A = dict_team_a['csum_prev_min_K_A']
    # predictors = [dict_team_a['csum_prev_min_K_A'] - dict_team_b['csum_prev_min_K_A'],
    #               dict_team_a['csum_prev_min_minions_killed'] - dict_team_b['csum_prev_min_minions_killed'],
    #               dict_team_a['csum_prev_min_total_gold'] - dict_team_a['csum_prev_min_total_gold']]
    for predictor_stat in predictor_stats:
        dict_team_difference = dict_team_a[predictor_stat] - dict_team_b[predictor_stat]
        game_predictor_stats.append(dict_team_difference)
    predictor_numpy_array = numpy.array([game_predictor_stats])
    return predictor_numpy_array


def get_predictors_in_numpy_arrays(team_stats_df, predictor_stats):
    games = get_predictors(team_stats_df)
    game_list = []
    y_array_list = []
    for game in games:
        game_predictor_stats = []
        if not (numpy.isnan(game['csum_prev_min_minions_killed']) and numpy.isnan(game['csum_prev_min_total_gold'])):
            # games_predictors = [game['csum_prev_min_K_A'], game['csum_prev_min_minions_killed'],
            #                     game['csum_prev_min_total_gold']]
            for predictor_stat in predictor_stats:
                game_predictor_stats.append(game[predictor_stat])
            game_list.append(game_predictor_stats)
            y_array_list.append(game['y_element'])
    predictors = numpy.array(game_list)
    y_array = numpy.array([y_array_list])
    # print("predictors is: {}".format(predictors))
    # print("y array is: {}".format(y_array))
    return (predictors, y_array)

def list_of_tuples_to_list(list_of_tuples_games):
    game_ids_all = []
    for begin_game_number, last_game_number in list_of_tuples_games:
        game_ids = list(range(begin_game_number, last_game_number))
        game_ids_all = game_ids_all + game_ids
    return game_ids_all


def check_cache(game_ids_all):
    last_game_number = game_ids_all[-1]
    conn = create_engine('postgresql://postgres:postgres@localhost:5432/postgres')
    has_game_stats_table = conn.has_table('team_stats')
    if has_game_stats_table:
        df_game_stats = pandas.read_sql_table('team_stats', conn)
        print('game_ids_all is {}'.format(game_ids_all))
        df_game_stats_all = df_game_stats[df_game_stats.game_id.isin(game_ids_all)]
        # Using game_numbers here since we need the last few games to check.
        max_game_id_cached = df_game_stats_all['game_id'].max()
        print('max_game_id is: {}'.format(max_game_id_cached))
        if pandas.isnull(max_game_id_cached):
            print('max_game_id is nan changing to: {}'.format(game_ids_all[0]))
            max_game_id_cached = game_ids_all[0]
        # Check if all the game numbers have been cached, if not return what game to start form and what game to end from.
        if max_game_id_cached != last_game_number:
            print('not everything is cached retrieve from game_ids: {}'.format(game_ids_all))
            # Get the index of the max_game_id
            max_game_id_index = game_ids_all.index(max_game_id_cached)
            # Trim down the list to only the games that need to be retrieved, start from the max_id + 1 because we don't
            # want to count max_id we already have it
            game_ids_to_find = game_ids_all[max_game_id_index:]
            team_stats_df = get_team_stats_in_dataframe(game_ids_to_find)
            team_stats_df.to_sql('team_stats', conn, if_exists='append')
            team_stats_df = pandas.concat([df_game_stats_all, team_stats_df])
            return team_stats_df
        else:
            # If everything was cached return cached as true and just return the last numbers
            # I could do this part better.
            print("everything cached no need to retrieve from api")
            return df_game_stats_all
    else:
        # Table did not exist, have to get all
        team_stats_df = get_team_stats_in_dataframe(game_ids_all)
        print('table does not exist inserting full table')
        team_stats_df.to_sql('team_stats', conn)
        print('table inserted')
        return team_stats_df


def get_team_stats_df(game_ids_all, has_cache=False):
    if has_cache:
        team_stats_df = check_cache(game_ids_all)
    else:
        team_stats_df = get_team_stats_in_dataframe(game_ids_all)
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
            game_stat_predictor_dict['eff_{}'.format(key_stat)] = red_team['eff_{}'.
                format(key_stat)] - blue_team['eff_{}'.format(key_stat)]
        game_stat_predictor_dict['csum_prev_kda'] = red_team['csum_prev_kda'] - blue_team['csum_prev_kda']
        game_stat_predictor_dict['game_id'] = red_team['game_id']
        if red_team['won_x']:
            game_stat_predictor_dict['y_element'] = 1
        elif blue_team['won_x']:
            game_stat_predictor_dict['y_element'] = 0
        game_stats_predictors.append(game_stat_predictor_dict)
    return game_stats_predictors


def get_team_stats_in_dataframe(game_ids_all):
    team_stats_df = None
    x = 0
    for game_id in game_ids_all:
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        game = json.loads(game_league)
        blue_team_id = game['contestants']['blue']['id']
        red_team_id = game['contestants']['red']['id']
        winner_id = game['winnerId']
        if game != ['Entity not found'] and game['gameLength'] is not None and \
                        game['players']['player0']['totalGold'] is not None:
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
        raise Exception("This is no winning team for blue team {} and red team {} and red game {} "
                        "and blue game {} and red won is: and blue won is:"
                        .format(blue_team['team_id'], red_team['team_id'], red_team['game_id'], blue_team['game_id']))
    return blue_team, red_team


def main():
    # NA and EU LCS
    # 6164, 6253
    # 6074, 6163
    predictor_stats = ['eff_minions_killed', 'eff_total_gold']
    # eu_games = list_of_tuples_to_list([(6074, 6163), (7061, 7065)])
    # na_games = list_of_tuples_to_list([(6164, 6253), (7067, 7071)])
    lcs_games = [6000, 6001, 6002, 6003, 6004, 6005, 6013, 6014, 6015, 6016, 6017, 6022, 6023, 6024, 6025, 6028, 6029,
                 6030, 6074, 6075, 6076, 6077, 6078, 6079, 6080, 6081, 6082, 6083, 6084, 6085, 6086, 6087, 6088, 6089,
                 6090, 6091, 6092, 6093, 6094, 6095, 6096, 6097, 6098, 6099, 6100, 6101, 6102, 6103, 6104, 6105, 6106,
                 6107, 6108, 6109, 6110, 6111, 6112, 6113, 6114, 6115, 6116, 6117, 6118, 6119, 6120, 6121, 6122, 6123,
                 6124, 6125, 6126, 6127, 6128, 6129, 6130, 6131, 6132, 6133, 6134, 6135, 6136, 6137, 6138, 6139, 6140,
                 6141, 6142, 6143, 6144, 6145, 6146, 6147, 6148, 6149, 6150, 6151, 6152, 6153, 6154, 6155, 6156, 6157,
                 6158, 6159, 6160, 6161, 6162, 6163, 6164, 6165, 6166, 6167, 6168, 6169, 6170, 6171, 6172, 6173, 6174,
                 6175, 6176, 6177, 6178, 6179, 6180, 6181, 6182, 6183, 6184, 6185, 6186, 6187, 6188, 6189, 6190, 6191,
                 6192, 6193, 6194, 6195, 6196, 6197, 6198, 6199, 6200, 6201, 6202, 6203, 6204, 6205, 6206, 6207, 6208,
                 6209, 6210, 6211, 6212, 6213, 6214, 6215, 6216, 6217, 6218, 6219, 6220, 6221, 6222, 6223, 6224, 6225,
                 6226, 6227, 6228, 6229, 6230, 6231, 6232, 6233, 6234, 6235, 6236, 6237, 6238, 6239, 6240, 6241, 6242,
                 6243, 6244, 6245, 6246, 6247, 6248, 6249, 6250, 6251, 6252, 6253, 7061, 7062, 7063, 7064, 7065, 7066,
                 7067, 7068, 7069, 7070, 7071, 7072, 7173, 7194, 7195, 7196, 7200, 7201, 7202, 7203, 7204, 7205, 7256,
                 7257, 7258, 7259, 7264, 7265, 7266, 7267, 7273, 7274, 7284, 7367, 7368, 7369, 7370, 7371, 7372, 7375,
                 7376, 7378, 7379, 7380, 7404, 7405, 7406, 7407, 7408, 7432, 7440, 7441, 7442, 7443, 7448, 7449, 7450,
                 7453, 7454, 7455, 7472, 7473, 7474, 7475, 7477, 7478, 7479, 7480, 7481, 7483, 7485, 7486, 7487, 7488,
                 7489, 7490, 7491, 7492, 7493, 7512, 7513, 7515, 7516, 7517, 7518, 7521, 7522, 7523, 7524, 7525]
    lck_games = [6006, 6007, 6008, 6009, 6049, 6050, 6064, 6065, 6066, 6067, 6068, 6069, 6070, 6071, 6072, 6073, 6254,
                 6255, 6256,  6426, 6427, 6428, 6429, 6430, 6431, 6432, 6433, 6434, 6435, 6436, 6437, 6438, 6439,
                 6440, 6441, 6442, 6443, 6444, 6445, 6446, 6447, 6448, 6449, 6450, 6451, 6452, 6453, 6454, 6455, 6456,
                 6457, 6458, 6459, 6460, 6461, 6462, 6463, 6464, 6465, 6466, 6467, 6468, 6469, 6470, 6471, 6472, 6473,
                 6608, 6609, 6616, 6617, 6624, 6625, 6626, 6631, 6632, 6633, 6690, 6691, 6715, 6716, 6717, 6728, 6729,
                 6738, 6739, 6740, 6749, 6757, 6758, 6759, 6764, 6765, 6766, 6767, 6778, 6779, 6780, 6787, 6788, 6791,
                 6822, 6823, 6840, 6841, 6842, 6843, 6939, 6940, 6943, 6944, 6951, 6954, 6955, 6962, 6963, 6972, 6973,
                 6974, 6975, 6976, 6977, 6978, 6979, 6980, 6981, 6982, 6983, 6984, 6985, 6986, 6987, 6988, 6989, 6990,
                 6991, 6992, 6993, 6994, 6995, 6996, 6997, 6998, 6999, 7000, 7001, 7002, 7003, 7004, 7005, 7006, 7007,
                 7008, 7009, 7010, 7011, 7012, 7013, 7014, 7015, 7016, 7017, 7018, 7021, 7022, 7023, 7026, 7027, 7039,
                 7040, 7054, 7055, 7058, 7076, 7077, 7086, 7087, 7105, 7106, 7107, 7110, 7111, 7114, 7115, 7116, 7117,
                 7118, 7119, 7125, 7126, 7127, 7128, 7129, 7130, 7131, 7132, 7133, 7144, 7145, 7146, 7151, 7152, 7153,
                 7154, 7155, 7156, 7157, 7159, 7160, 7161, 7162, 7163, 7178, 7179, 7185, 7206, 7207, 7208, 7209, 7214,
                 7215, 7220, 7221, 7222, 7235, 7236, 7237, 7240, 7245, 7246, 7247, 7250, 7251, 7252, 7254, 7318, 7319,
                 7322, 7323, 7347, 7357, 7358, 7359, 7360, 7361, 7362, 7400, 7403, 7413, 7414, 7415, 7416, 7417, 7418,
                 7467, 7468, 7494, 7495, 7497, 7499, 7500, 7502, 7507, 7508, 7510, 7526, 7527, 7528, 7529, 7530, 7531]
    # lpl_games = [6010, 6011, 6012, 6018, 6019, 6020, 6021, 6476, 6477, 6478, 6479, 6480, 6481, 6482, 6483, 6484, 6485,
    #              6486, 6487, 6488, 6489, 6490, 6491, 6492, 6493, 6494, 6495, 6496, 6497, 6498, 6499, 6500, 6501, 6502,
    #              6503, 6504, 6505, 6506, 6507, 6508, 6509, 6510, 6511, 6512, 6513, 6514, 6515, 6516, 6517, 6518, 6519,
    #              6520, 6521, 6522, 6523, 6524, 6525, 6526, 6527, 6528, 6529, 6530, 6531, 6532, 6533, 6534, 6535, 6536,
    #              6537, 6538, 6539, 6540, 6541, 6542, 6543, 6544, 6545, 6546, 6547, 6548, 6549, 6550, 6551, 6552, 6553,
    #              6554, 6555, 6556, 6557, 6558, 6559, 6560, 6561, 6562, 6563, 6564, 6565, 6566, 6567, 6568, 6569, 6570,
    #              6571, 6572, 6573, 6574, 6575, 6576, 6577, 6578, 6579, 6580, 6581, 6582, 6583, 6584, 6585, 6586, 6587,
    #              6588, 6589, 6590, 6591, 6592, 6593, 6594, 6595, 6596, 6597, 6598, 6599, 6600, 6601, 6602, 6603, 6604,
    #              6605, 6606, 6607, 6612, 6613, 6614, 6615, 6620, 6621, 6622, 6623, 6627, 6628, 6629, 6630, 6718, 6719,
    #              6720, 6721, 6724, 6725, 6726, 6727, 6732, 6733, 6734, 6735, 6753, 6754, 6755, 6756, 6768, 6769, 6770,
    #              6771, 6772, 6773, 6774, 6775, 6826, 6827, 6828, 6829, 6830, 6831, 6838, 6839, 6844, 6845, 6846, 6847,
    #              6947, 6948, 6949, 6950, 6958, 6959, 6960, 6961, 6968, 6969, 6970, 6971, 7028, 7029, 7030, 7031, 7041,
    #              7044, 7045, 7047, 7050, 7051, 7052, 7053, 7073, 7074, 7075, 7080, 7083, 7084, 7085, 7089, 7091, 7092,
    #              7093, 7094, 7134, 7135, 7136, 7137, 7138, 7139, 7140, 7143, 7147, 7148, 7149, 7150, 7164, 7165, 7168,
    #              7172, 7174, 7177, 7184, 7187, 7188, 7189, 7192, 7193, 7210, 7211, 7212, 7213, 7216, 7217, 7218, 7219,
    #              7223, 7224, 7225, 7226, 7241, 7242, 7243, 7244, 7248, 7249, 7253, 7255, 7260, 7261, 7262, 7263, 7285,
    #              7286, 7287, 7288, 7289, 7290, 7291, 7292, 7293, 7294, 7295, 7296, 7297, 7298, 7299, 7300, 7301, 7302,
    #              7303, 7304, 7305, 7306, 7307, 7308, 7309, 7310, 7311, 7312, 7313, 7315, 7316, 7324, 7325, 7328, 7329,
    #              7330, 7331, 7332, 7352, 7353, 7354, 7355, 7356, 7381, 7382, 7383, 7384, 7385, 7386, 7387, 7392, 7395,
    #              7396, 7397, 7398, 7399, 7409, 7410, 7411, 7444, 7445, 7446, 7447]
    lms_games = [6370, 6371, 6372, 6373, 6374, 6375, 6376, 6377, 6378, 6379, 6380, 6381, 6382, 6383, 6384, 6385, 6386,
                 6387, 6388, 6389, 6390, 6391, 6392, 6393, 6394, 6395, 6396, 6397, 6398, 6399, 6400, 6401, 6402, 6403,
                 6404, 6405, 6406, 6407, 6408, 6409, 6410, 6411, 6412, 6413, 6414, 6415, 6416, 6417, 6418, 6419, 6420,
                 6421, 6422, 6423, 6424, 6425, 6474, 6475, 6610, 6611, 6618, 6619, 6634, 6635, 6692, 6711, 6722, 6723,
                 6741, 6742, 6750, 6751, 6762, 6763, 6782, 6783, 6789, 6790, 6824, 6825, 6941, 6942, 6945, 6946, 6956,
                 6957, 7019, 7020, 7024, 7025, 7032, 7033, 7034, 7035, 7048, 7049, 7056, 7057, 7059, 7060, 7078, 7079,
                 7088, 7090, 7095, 7096, 7108, 7109, 7112, 7113, 7120, 7121, 7122, 7123, 7124, 7169, 7170, 7171, 7180,
                 7181, 7186, 7190, 7191, 7197, 7198, 7199, 7363, 7364, 7365, 7366, 7373, 7374, 7388, 7389, 7390, 7391]
    iwc_games = [7419, 7420, 7421, 7422, 7423, 7424, 7425, 7426, 7427, 7428, 7429, 7430, 7431, 7433, 7434, 7435, 7436,
                 7437, 7438, 7439, 7469, 7470, 7471, 7484, 7519, 7520]
    lcs_team_df = get_team_stats_df(lcs_games, has_cache=True)
    lck_team_df = get_team_stats_df(lck_games, has_cache=True)
    # lpl_team_df = get_team_stats_df(lpl_games, has_cache=True)
    lms_team_df = get_team_stats_df(lms_games, has_cache=True)
    iwc_team_df = get_team_stats_df(iwc_games, has_cache=True)
    lcs_predictors, lcs_y_array = get_predictors_in_numpy_arrays(lcs_team_df, predictor_stats)
    lck_predictors, lck_y_array = get_predictors_in_numpy_arrays(lck_team_df, predictor_stats)
    # lpl_predictors, lpl_y_array = get_predictors_in_numpy_arrays(lpl_team_df, predictor_stats)
    lms_predictors, lms_y_array = get_predictors_in_numpy_arrays(lms_team_df, predictor_stats)
    iwc_predictors, iwc_y_array = get_predictors_in_numpy_arrays(iwc_team_df, predictor_stats)
    # Need to use concatenate for the predictors because we need an array of an arrays with predictors in each array
    predictors = numpy.concatenate((lcs_predictors, lck_predictors,  lms_predictors,
                                    iwc_predictors))
    # need to use append because we need an array of 0 and 1's
    y_array = numpy.append(lcs_y_array, lck_y_array)
    y_array = numpy.append(y_array, lms_y_array)
    y_array = numpy.append(y_array, iwc_y_array)
    logreg = train_model(predictors, y_array)
    lolgreg_standard, scaler = train_model_standard_scaler(predictors, y_array)
    test_model(predictors, y_array)
    # CLG vs TSM
    real_array = get_latest_team_stats_numpy_array(2, 1, lcs_team_df, predictor_stats)
    predict_on_model(logreg, real_array, 'CLG')
    # Fnatic vs Origen
    real_array = get_latest_team_stats_numpy_array(68, 3862, lcs_team_df, predictor_stats)
    predict_on_model(logreg, real_array, 'Fnatic')

if __name__ == "__main__":
    main()
