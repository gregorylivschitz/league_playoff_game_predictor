import pandas
from sqlalchemy.orm import sessionmaker
from entities.league_of_legends_entities import Game, Player

__author__ = 'Greg'


class PredictPlayerStats:

    def __init__(self, engine, player_name):
        self.engine = engine
        self.player_name = player_name
        Session = sessionmaker(bind=engine)
        self.session = Session()

    def _get_game_ids_from_database(self):
        game_ids_row = self.session.query(Game.id)
        game_ids = [game[0] for game in game_ids_row]
        return game_ids

    def _get_game_by_ids(self, game_ids):
        return self.session.query(Game).filter(Game.id.in_(game_ids))

    def _get_player_id_by_player_name(self, team_name):
        team = self.session.query(Player).filter(Player.name.__eq__(team_name))
        return team[0].id

    def _get_processed_player_stats_in_df(self):
        game_ids = self._get_game_ids_from_database()
        last_game_number = game_ids[-1]
        has_processed_team_stats_table = self.engine.has_table(self.processed_team_stats_table_name)
        if has_processed_team_stats_table:
            df_game_stats = pandas.read_sql_table(self.processed_team_stats_table_name, self.engine)
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
        self.processed_team_stats_df = pandas.read_sql_table(self.processed_team_stats_table_name, self.engine)