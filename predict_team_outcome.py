from operator import itemgetter
import pandas
import numpy
from sklearn import linear_model, cross_validation, preprocessing
import sys
from entities.league_of_legends_entities import Game, Team

__author__ = 'Greg'
# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}


class PredictTeamWin():

    def __init__(self, session, engine, blue_team_name, red_team_name,
                 predictor_stats=('csum_prev_min_K_A', 'csum_prev_min_minions_killed', 'csum_prev_min_total_gold')):
        self.team_stats_df = None
        self.logreg = linear_model.LogisticRegression()
        self.red_team_name = red_team_name
        self.blue_team_name = blue_team_name
        self.conn = engine
        self.session = session
        self.team_stats_table_name = 'team_stats_df'
        self.processed_team_stats_table_name = 'processed_team_stats_df'
        self.predictor_stats = predictor_stats
        self.key_stats = ('kills', 'deaths', 'assists', 'minions_killed', 'total_gold',
                         'K_A', 'A_over_K')
        self._process_team_stats_and_train()



    def _process_team_stats_and_train(self):
        self._get_processed_team_stats_in_data_frame()
        self._get_latest_team_stats_numpy_array()
        self._get_predictors_in_numpy_arrays()
        self._train_model()


    def _get_game_ids_from_database(self):
        game_ids_row = self.session.query(Game.id)
        game_ids = [game[0] for game in game_ids_row]
        return game_ids

    def _get_game_by_ids(self, game_ids):
        return self.session.query(Game).filter(Game.id.in_(game_ids))

    def _get_team_id_by_team_name(self, team_name):
        team = self.session.query(Team).filter(Team.name.__eq__(team_name))
        return team[0].id

    def _get_processed_team_stats_in_data_frame(self):
        game_ids = self._get_game_ids_from_database()
        last_game_number = game_ids[-1]
        has_processed_team_stats_table = self.conn.has_table(self.processed_team_stats_table_name)
        if has_processed_team_stats_table:
            df_game_stats = pandas.read_sql_table(self.processed_team_stats_table_name, self.conn)
            df_game_stats_all = df_game_stats[df_game_stats.game_id.isin(game_ids)]
            # Using game_numbers here since we need the last few games to check.
            max_game_id_cached = df_game_stats_all['game_id'].max()
            if pandas.isnull(max_game_id_cached):
                max_game_id_cached = game_ids[0]
            # Check if all the game numbers have been cached,
            # if not return what game to start form and what game to end from.
            if max_game_id_cached != last_game_number:
                # Get the index of the max_game_id
                max_game_id_index = game_ids.index(max_game_id_cached)
                # Trim down the list to only the games that need to be retrieved,
                # start from the max_id + 1 because we don't
                # want to count max_id we already have it
                game_ids_to_find = game_ids[max_game_id_index:]
                games = self._get_game_by_ids(game_ids_to_find)
                team_stats_df = self._get_team_stats_in_df(games)
                self._insert_into_team_stats_df_tables(team_stats_df)
            else:
                # If everything was cached return cached as true and just return the last numbers
                # I could do this part better.
                print("everything cached no need to retrieve from api")
        else:
            # Table did not exist, have to get all
            games = self._get_game_by_ids(game_ids)
            team_stats_df = self._get_team_stats_in_df(games)
            print('table does not exist inserting full table')
            self._insert_into_team_stats_df_tables(team_stats_df)
            print('table inserted')
        self.processed_team_stats_df = pandas.read_sql_table(self.processed_team_stats_table_name, self.conn)

    def _insert_into_team_stats_df_tables(self, team_stats_df):
        team_stats_df.to_sql(self.team_stats_table_name, self.conn, if_exists='append')
        processed_team_stats_df = self._process_team_stats_df(team_stats_df)
        processed_team_stats_df.to_sql(self.processed_team_stats_table_name, self.conn, if_exists='append')

    def _get_team_stats_in_df(self, games):
        counter = 0
        for game in games:
            blue_team, red_team = self._convert_game_to_game_df(game)
            blue_team_df = pandas.DataFrame(blue_team, index=[counter])
            red_team_df = pandas.DataFrame(red_team, index=[counter + 1])
            if self.team_stats_df is None:
                self.team_stats_df = blue_team_df.append(red_team_df)
            else:
                self.team_stats_df = self.team_stats_df.append(blue_team_df.append(red_team_df))
            counter += 2
        return self.team_stats_df

    # Need to get it to look like this:
    # {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
    # 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
    # 'minions_killed': 783}
    @staticmethod
    def _convert_game_to_game_df(game):
        if game.team_stats[0].color == 'blue':
            blue_team_stats = dict(game.team_stats[0].__dict__)
            blue_team_stats['team_name'] = game.team_stats[0].team.name
            red_team_stats = dict(game.team_stats[1].__dict__)
            red_team_stats['team_name'] = game.team_stats[1].team.name
        else:
            blue_team_stats = dict(game.team_stats[1].__dict__)
            blue_team_stats['team_name'] = game.team_stats[1].team.name
            red_team_stats = dict(game.team_stats[0].__dict__)
            red_team_stats['team_name'] = game.team_stats[0].team.name
        del blue_team_stats['_sa_instance_state']
        del red_team_stats['_sa_instance_state']
        blue_team_stats['game_length_minutes'] = float(game.game_length_minutes)
        red_team_stats['game_length_minutes'] = float(game.game_length_minutes)
        blue_team_stats['total_gold'] = float(blue_team_stats['total_gold'])
        red_team_stats['total_gold'] = float(red_team_stats['total_gold'])
        return blue_team_stats, red_team_stats


    def _process_team_stats_df(self, team_stats_df):
        team_stats_df = team_stats_df.sort(['game_id', 'team_id'])
        key_stats = ['game_number', 'game_length_minutes', 'kills', 'deaths', 'assists', 'minions_killed', 'total_gold',
                     'K_A', 'A_over_K']
        team_stats_df['K_A'] = \
            team_stats_df['kills'] + team_stats_df['assists']
        team_stats_df['A_over_K'] = \
            team_stats_df['assists'] / team_stats_df['kills']
        team_grouped_by_game_id_df = team_stats_df.groupby(['game_id'], as_index=False).sum()
        team_stats_df = pandas.merge(team_stats_df, team_grouped_by_game_id_df, on=['game_id'])
        team_stats_df.to_sql('calc_team_stats', self.conn, if_exists='append')
        for key_stat in key_stats:
            # Need to add x/y to the keystat because when I add the groupby and merge the keystats get x and y added
            # to them at the end since they are the same name
            key_stat_x = '{}_x'.format(key_stat)
            key_stat_y = '{}_y'.format(key_stat)
            team_stats_df['csum_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id_x')[key_stat_x].cumsum()
            team_stats_df['csum_total_{}'.format(key_stat)] = team_stats_df.groupby(by='team_id_x')[key_stat_y].cumsum()
            team_stats_df['csum_prev_{}'.format(key_stat)] = team_stats_df['csum_{}'.format(key_stat)] - team_stats_df[
                key_stat_x]
            team_stats_df['csum_total_prev_{}'.format(key_stat)] = \
                team_stats_df['csum_total_{}'.format(key_stat)] - team_stats_df[key_stat_y]
            team_stats_df['csum_prev_avg_{}'.format(key_stat)] = \
                team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_prev_game_number']
            team_stats_df['per_min_{}'.format(key_stat)] = team_stats_df[key_stat_x] / team_stats_df[
                'game_length_minutes_x']
            team_stats_df['csum_prev_percent_{}'.format(key_stat)] = \
                team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_total_prev_{}'.format(key_stat)]
            team_stats_df['margin_{}'.format(key_stat)] = \
                team_stats_df['csum_prev_percent_{}'.format(key_stat)] - (
                    1 - team_stats_df['csum_prev_percent_{}'.format(key_stat)])
            team_stats_df['eff_{}'.format(key_stat)] = \
                team_stats_df['csum_prev_percent_{}'.format(key_stat)] / (
                    1 - team_stats_df['csum_prev_percent_{}'.format(key_stat)])
            if key_stat not in ['game_number', 'game_length_minutes']:
                team_stats_df['csum_min_{}'.format(key_stat)] = \
                    team_stats_df['csum_{}'.format(key_stat)] / team_stats_df['csum_game_length_minutes']
                team_stats_df['csum_prev_min_{}'.format(key_stat)] = \
                    team_stats_df['csum_prev_{}'.format(key_stat)] / team_stats_df['csum_prev_game_length_minutes']
        team_stats_df['csum_prev_kda'] = team_stats_df['csum_prev_kills'] * team_stats_df['csum_prev_assists'] \
                                         / team_stats_df['csum_prev_deaths']
        team_stats_df = team_stats_df.sort(['game_id'])
        return team_stats_df

    def _get_predictors_in_numpy_arrays(self):
        games = self._get_predictors()
        game_list = []
        y_array_list = []
        for game in games:
            game_predictor_stats = []
            if not (numpy.isnan(game['csum_prev_min_minions_killed']) and numpy.isnan(game['csum_prev_min_total_gold'])):
                for predictor_stat in self.predictor_stats:
                    game_predictor_stats.append(game[predictor_stat])
                game_list.append(game_predictor_stats)
                y_array_list.append(game['y_element'])
        self.predictors = numpy.array(game_list)
        self.y_array = numpy.array([y_array_list])
        # print("predictors are: {}".format(predictors))
        # print("y array is: {}".format(y_array))
        return self.predictors, self.y_array

    def _get_predictors(self):
        team_records = self.processed_team_stats_df.to_dict('records')
        game_stats_predictors = []
        team_records.sort(key=itemgetter('game_id'))
        for team_index in range(0, len(team_records), 2):
            team_1 = team_records[team_index]
            team_2 = team_records[team_index + 1]
            if team_1['color'] == 'blue' and team_2['color'] == 'red':
                blue_team = team_records[team_index]
                red_team = team_records[team_index + 1]
            elif team_1['color'] == 'red' and team_2['color'] == 'blue':
                red_team = team_records[team_index]
                blue_team = team_records[team_index + 1]
            else:
                raise Exception("Need both a blue and a red team in the game have blue "
                                "team: {} and red team: {}".format(team_1['color'], team_2['color']))
            if blue_team['game_id'] != red_team['game_id']:
                raise Exception('Huge problem game_id''s for teams did not match winning_team game_id: {} '
                                'losing_team game_id: {}'.format(blue_team, red_team))
            game_stat_predictor_dict = {}
            for key_stat in self.key_stats:
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

    def _train_model(self):
        y_1darray = numpy.squeeze(self.y_array)
        self.logreg.fit(self.predictors, y_1darray)

    def test_model(self):
        scores = cross_validation.cross_val_score(self.logreg, self.predictors, self.y_array, cv=5)
        print("Accuracy: %0.2f (+/- %0.2f)" % (scores.mean(), scores.std() * 2))

    def _get_latest_team_stats_numpy_array(self):
        red_team_id = self._get_team_id_by_team_name(self.red_team_name)
        blue_team_id = self._get_team_id_by_team_name(self.blue_team_name)
        game_predictor_stats = []
        # team_stats_df.to_csv('test_team_stats')
        # team_stats_df = team_stats_df[team_stats_df.team_id.isin([2, 1])]
        team_stats_df_red = self.processed_team_stats_df[self.processed_team_stats_df['team_id_x'] == red_team_id]
        team_stats_df_blue = self.processed_team_stats_df[self.processed_team_stats_df['team_id_x'] == blue_team_id]
        team_stats_df_red = team_stats_df_red.sort(['game_id'], ascending=False).head(1)
        team_stats_df_blue = team_stats_df_blue.sort(['game_id'], ascending=False).head(1)
        dict_team_red = team_stats_df_red.to_dict('records')[0]
        dict_team_blue = team_stats_df_blue.to_dict('records')[0]
        for predictor_stat in self.predictor_stats:
            dict_team_difference = dict_team_red[predictor_stat] - dict_team_blue[predictor_stat]
            game_predictor_stats.append(dict_team_difference)
        self.predictor_numpy_array = numpy.array([game_predictor_stats])

    def predict_on_single_game(self):
        print('logistical regression outcome for {} is: {}'.format(self.red_team_name, self.logreg.predict(self.predictor_numpy_array)))
        probability_in_numpy_array = self.logreg.predict_proba(self.predictor_numpy_array)
        return {self.blue_team_name: probability_in_numpy_array[0][0], self.red_team_name: probability_in_numpy_array[0][1]}

        # numpy_array = self.logreg.predict_proba(real_array)
        # proba_list = numpy_array.tolist()[0]
        # turn_game_proba_into_series(5, 3, proba_list[1], team_name)