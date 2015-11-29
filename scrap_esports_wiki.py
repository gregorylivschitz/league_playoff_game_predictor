from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup, NavigableString
import requests
from entities.league_of_legends_entities import DataSource, Game, Team, TeamStats
from utilities.sqlalchemy import get_or_create

__author__ = 'Greg'


# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}

# # Things we need real_name instead of team_name, team_id, game_id
# [({'total_gold': 48300.0, 'won': False, 'color': 'blue', 'game_length_minutes': '33.32', 'deaths': 9, 'minions_killed': 952, 'assists': 11, 'team_name': 'Team WE', 'kills': 6},
# {'total_gold': 48300.0, 'won': True, 'color': 'red', 'game_length_minutes': '33.32', 'deaths': 6, 'minions_killed': 1089, 'assists': 29, 'team_name': 'Invictus Gaming', 'kills': 9})

# What player stats should look like
# [{'game_id': 500, 'player_name': 'xPeke', 'kills': 2, 'deaths': 3, 'assists': 5, 'gold': 20000, 'minions_killed': 370, 'color': blue},
# {'game_id': 500, 'player_name': 'xPeke', 'kills': 2, 'deaths': 3, 'assists': 5, 'gold': 20000, 'minions_killed': 370, 'color': blue}]

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid')
Session = sessionmaker(bind=engine)
session = Session()

# def merge_player_and_game_info(soup):
#     players, game_info = parse_recap_tables_for_players(soup)
#     game_merge = []

def merge_game_and_game_info(soup, data_source):
    games, games_info = parse_recap_tables_for_games(soup, data_source)
    if len(games) != len(games_info):
        raise ValueError('merging error games and games_info did not match something is wrong with the html')
    games_merge = []
    for game_index, game in enumerate(games):
        game_blue_team, game_red_team = game
        game_info_blue_team, game_info_red_team = games_info[game_index]
        game_blue_merged = dict(list(game_blue_team.items()) + list(game_info_blue_team.items()))
        game_red_merged = dict(list(game_red_team.items()) + list(game_info_red_team.items()))
        games_merge.append((game_blue_merged, game_red_merged))
    return games_merge


# parse recap tables into a list of team tuples
def parse_recap_tables_for_games(soup, data_source):
    game = Game()
    for recap_table in soup.find_all("table", {"class": "wikitable matchrecap1"}):
        game = parse_game_info(recap_table, game)
        games.append(parse_game(recap_table, game))
    # return games, games_info


# given a column, get contents and strip garbage
def parse_column_stats(col):
    # assume col.contents has value we want at index 0
    return int(str(col.contents[0]).strip())


def parse_column_player_name(col):
    # assume col.contents has value we want at index 0
    return str(col.contents[1].contents[0]).strip()


def parse_champion_name(col):
    return str(col.contents[0]['title'].strip())


# parse values from table and add to team
def parse_player_stats_add_to_team(team, player_stat_table):
    rows = player_stat_table.find_all("tr")
    player = parse_player_stats(player_stat_table)
    # assume len(cols) == 11
    team['minions_killed'] += player['minions_killed']
    team['assists'] += player['assists']
    team['deaths'] += player['deaths']
    team['kills'] += player['kills']
    team['game_number'] = 1
    return team


def parse_player_stats(player_stat_table):
    rows = player_stat_table.find_all("tr")
    # assume len(row) == 1
    row = rows[0]
    cols = row.find_all('td')
    # print('The col is {} and the stat is {}'.format(3, parse_column(cols[3])))
    player = {'player_name': parse_column_player_name(cols[1]), 'champion_played': parse_champion_name(cols[0]),
              'minions_killed': parse_column_stats(cols[10]), 'assists': parse_column_stats(cols[6]),
              'deaths': parse_column_stats(cols[5]), 'kills': parse_column_stats(cols[4])}
    return player

def parse_player_stats_with_color(color, game_table):
    player_stats_tables = game_table.find_all("table", {"class": "prettytable"})
    player = parse_player_stats(player_stats_tables)
    player['color'] = color
    return player


# color, game_table to
# {'color': 'blue', 'assists': 37, 'deaths': 5, 'kills': 16,'minions_killed': 783}
def parse_team_game(game_table):
    team = {'color': color, 'assists': 0, 'deaths': 0, 'kills': 0, 'minions_killed': 0}
    player_stats_tables = game_table.find_all("table", {"class": "prettytable"})
    for player_stat_table in player_stats_tables:
        parse_player_stats_add_to_team(team, player_stat_table)
    return team


# list of tables to
# ( {'color': 'blue', 'assists': 37,'deaths': 5, 'kills': 16,'minions_killed': 783}, {'color': 'red', 'assists': 37,
# 'deaths': 5, 'kills': 16, 'minions_killed': 783})
def parse_game(recap_tables, game):
    # len(game_tables) == 3 assumption
    # game_tables[0] skip
    # game_tables[1] is blue team
    # game_tables[2] is red team
    game_tables = recap_tables.find_all("table", {"class": "prettytable matchrecap2"})
    if game.teams[0].team_stats.color == 'blue':
        parse_team_game('blue', game_tables[1])
    else:
        parse_team_game('red', game_tables[2])
    return

def parse_player(recap_tables):
    game_tables = recap_tables.find_all("table", {"class": "prettytable matchrecap2"})
    return parse_team_game('blue', game_tables[1]), parse_team_game('red', game_tables[2])

def parse_game_info(recap_table, game):
    # should only be 1 info_table
    game_info_table = recap_table.find("table", {"class": "wikitable matchrecap2"})
    blue_team = parse_team_game_info('blue', game_info_table, game)
    red_team = parse_team_game_info('red', game_info_table, game)
    game.teams.append(blue_team)
    game.teams.append(red_team)
    print(game)
    return game


def parse_team_game_info(color, game_info_table, game):
    # team = {'color': color, 'total_gold': 0, 'team_name': '', 'game_length_minutes': 0, 'won': None}
    team_stats = TeamStats()
    team_stats.color = color
    rows = game_info_table.find_all('tr')
    # row where team name is kept and how we determine the win vs the loss
    row_game_info = rows[1]
    cols = row_game_info.find_all('td')
    rows_game_stats_info = rows[3]
    cols_game_stats_info = rows_game_stats_info.find_all('td')
    # team['game_length_minutes'] = float(cols_game_stats_info[5].contents[0].strip().replace(':', '.').replace('!', '1'))
    game.game_length_minutes = float(cols_game_stats_info[5].contents[0].strip().replace(':', '.').replace('!', '1'))
    # cols[0] = blue team_name, cols[1] = blue win or loss, cols[3] = red team name, cols[2] = red won or losee
    if team_stats.color == 'blue':
        team_name = cols[0].contents[0].strip()
        team = get_or_create(session, Team, external_name=team_name)
        team_stats.total_gold = float(cols_game_stats_info[10].contents[0].strip().replace('k', '')) * 1000
        try:
            if cols[1]['style'] == 'background-color:#ccffcc':
                team_stats.won = True
        except KeyError:
            team_stats.won = False
    elif team_stats.color == 'red':
        team_name = cols[3].contents[0].strip()
        team = get_or_create(session, Team, external_name=team_name)
        team_stats.total_gold = float(cols_game_stats_info[0].contents[2].strip().replace('k', '')) * 1000
        try:
            if cols[2]['style'] == 'background-color:#ccffcc':
                team_stats.won = True
        except KeyError:
            team_stats.won = False
    team.team_stats.append(team_stats)
    print(team)
    return team


def assign_game_id_and_team_id(all_merge_games, game_ids, team_name_ids):
    for index, merge_game in enumerate(all_merge_games):
        blue_team, red_team = merge_game
        red_team['game_id'] = game_ids[index]
        blue_team['game_id'] = game_ids[index]
        red_team['team_id'] = team_name_ids[red_team['team_name']]
        blue_team['team_id'] = team_name_ids[blue_team['team_name']]
        all_merge_games[index] = (red_team, blue_team)
    return all_merge_games


# def get_games_from_lpl_webpage(game_ids):
#     lpl_team_id_mapping = {'Oh My God': 10000, 'Unlimited Potential': 10001, 'Masters 3': 10002, 'Vici Gaming': 10003,
#                            'Royal Never Give Up': 10004, 'Team WE': 10005, 'EDward Gaming': 10006, 'LGD Gaming': 10007,
#                            'Team King': 10008, 'Invictus Gaming': 10009, 'Qiao Gu Reapers': 10010,
#                            'Snake eSports': 10011}
#     pages = 11
#     web_page = 'http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards'
#     print(get_lpl_web_pages(web_page, pages, game_ids, lpl_team_id_mapping))
#     return get_lpl_web_pages(web_page, pages, game_ids, lpl_team_id_mapping)

def get_players_from_worlds_webpage(game_id_initial, base_page, pages):
    for page in pages:
        web_page = '{}{}'.format(base_page, page)
        response = requests.get(web_page)
        text = response.text
        soup = BeautifulSoup(text)


def get_games_from_webpage(base_page=None, pages=None):
    all_merge_games = []
    for page in pages:
        web_page = '{}{}'.format(base_page, page)
        data_source = session.query(DataSource).filter(DataSource.external_location == web_page).first()
        if data_source is None:
            retrieved_data_source = DataSource(name='WEB', external_location=web_page)
            session.add(retrieved_data_source)
            response = requests.get(web_page)
            text = response.text
            soup = BeautifulSoup(text)
            merge_games = merge_game_and_game_info(soup, retrieved_data_source)
            all_merge_games += merge_games
        else:
            print('Webpage {} is already processed'.format(web_page))
        # for merge_game in merge_games:
        #     if team_mappings.get(merge_game[0]['team_name']) is not None:
        #         merge_game[0]['team_name'] = team_mappings[merge_game[0]['team_name']]
        #     if team_mappings.get(merge_game[1]['team_name']) is not None:
        #         merge_game[1]['team_name'] = team_mappings[merge_game[1]['team_name']]
    session.commit()
    #all_merge_games_with_game_id = assign_game_id_and_team_id(all_merge_games, game_ids, team_id_mapping)
    #print(all_merge_games_with_game_id)
    #return all_merge_games_with_game_id


def main():
    get_games_from_webpage(base_page='http://lol.esportspedia.com/wiki/2015_Season_World_Championship/Scoreboards',
                           pages = ['', '/Group_Stage/Group_B', '/Group_Stage/Group_C', '/Group_Stage/Group_D', '/Bracket_Stage']
    )


if __name__ == "__main__":
    main()
