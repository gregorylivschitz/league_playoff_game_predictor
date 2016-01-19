from decimal import Decimal
import decimal
import re
import traceback
from sqlalchemy import create_engine
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from bs4 import BeautifulSoup, NavigableString
import requests
from entities.league_of_legends_entities import DataSource, Game, Team, TeamStats, Player, PlayerStats, Tournament
from utilities.sqlalchemy import get_or_create
from urllib.parse import urlparse

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
Session = sessionmaker(bind=engine, autoflush=False)
session = Session()


def process_data_source(soup, data_source, tournament):
    data_source = parse_recap_tables_for_games(soup, data_source, tournament)
    return data_source


# parse recap tables into a list of team tuples
def parse_recap_tables_for_games(soup, data_source, tournament):
    for recap_table in soup.find_all("table", {"class": "wikitable matchrecap1"}):
        blue_team, red_team, game = parse_game_info(recap_table)
        session.add(game)
        parsed_game = parse_game(blue_team, red_team, game, recap_table)
        data_source.games.append(parsed_game)
        tournament.games.append(parsed_game)
    return data_source


# given a column, get contents and strip garbage
def parse_column_stats(col):
    # assume col.contents has value we want at index 0
    return int(str(col.contents[0]).strip())


def parse_gold_stat(col):
    return Decimal(str(col.contents[0]).strip().replace('k', '')) * 1000


def parse_column_player_name(col):
    # assume col.contents has value we want at index 0
    return str(col.contents[1].contents[0]).strip()


def parse_champion_name(col):
    return str(col.contents[0]['title'].strip())


def get_tournament_from_web_page(web_page):
    regions = ['LCK', 'LPL', 'LMS']
    url_parsed = urlparse(web_page)
    path = url_parsed.path
    # regex out the name of the tournament from the path
    p = re.compile('\/wiki\/(.+)\/Scoreboards')
    tournament_path = p.search(path).group(1)
    if 'League_Championship' in tournament_path:
        name, region, year, season = tournament_path.split('/')
        year = remove_season(year)
        season = remove_season(season)
        tournament = Tournament(name=name, region=region, year=int(year), season=season)
    elif any(region in tournament_path for region in regions):
        region, year, season = tournament_path.split('/')
        name = region
        year = remove_season(year)
        season = remove_season(season)
        tournament =Tournament(name=name, region=region, year=int(year), season=season)
    elif 'World_Championship' in tournament_path:
        tournament_split = tournament_path.split('_')
        year = tournament_split[0]
        name = '{}_{}'.format(tournament_split[2], tournament_split[3])
        region = 'ALL'
        season = tournament_split[2]
        tournament = Tournament(name=name, region=region, year=int(year), season=season)
    return tournament


def remove_season(path_string):
    path_string = path_string.replace('_Season', '')
    return path_string


# parse values from table and add to team
def parse_player_stats_add_to_team(game, team, team_stat,  player_stat_table):
    player_stat = parse_player_stats(game, team, player_stat_table)
    # assume len(cols) == 11
    team_stat.minions_killed += player_stat.minions_killed
    team_stat.assists += player_stat.assists
    team_stat.deaths += player_stat.deaths
    team_stat.kills += player_stat.kills
    team_stat.gold += player_stat.gold
    team_stat.game_number = 1
    return team_stat


def parse_player_stats(game, team, player_stat_table):
    rows = player_stat_table.find_all("tr")
    # assume len(row) == 1
    row = rows[0]
    cols = row.find_all('td')
    name = parse_column_player_name(cols[1])
    player = get_or_create(session, Player, name=name)
    champion_played = parse_champion_name(cols[0])
    # Page was updated to include tokens, so the location of the stats were messed up, this handles both types of pages.
    try:
        gold = parse_gold_stat(cols[9])
        minions_killed = parse_column_stats(cols[10])
    except decimal.InvalidOperation:
        gold = parse_gold_stat(cols[10])
        minions_killed = parse_column_stats(cols[11])
    try:
        assists = parse_column_stats(cols[6])
        deaths = parse_column_stats(cols[5])
        kills = parse_column_stats(cols[4])
    except ValueError:
        assists = parse_column_stats(cols[7])
        deaths = parse_column_stats(cols[6])
        kills = parse_column_stats(cols[5])
    player_stat = PlayerStats(champion_played=champion_played, minions_killed=minions_killed, assists=assists,
                              deaths=deaths, kills=kills, gold=gold)
    # print('The col is {} and the stat is {}'.format(3, parse_column(cols[3])))
    session.add(player_stat)
    player.player_stats.append(player_stat)
    game.player_stats.append(player_stat)
    team.player_stats.append(player_stat)
    return player_stat

# color, game_table to
# {'color': 'blue', 'assists': 37, 'deaths': 5, 'kills': 16,'minions_killed': 783}
def parse_team_game(game, team, team_stat, game_table):
    player_stats_tables = game_table.find_all("table", {"class": "prettytable"})
    for player_stat_table in player_stats_tables:
        team_stat = parse_player_stats_add_to_team(game, team, team_stat, player_stat_table)
    return team_stat


# list of tables to
# ( {'color': 'blue', 'assists': 37,'deaths': 5, 'kills': 16,'minions_killed': 783}, {'color': 'red', 'assists': 37,
# 'deaths': 5, 'kills': 16, 'minions_killed': 783})
def parse_game(blue_team, red_team, game, recap_tables):
    # len(game_tables) == 3 assumption
    # game_tables[0] skip
    # game_tables[1] is blue team
    # game_tables[2] is red team
    game_tables = recap_tables.find_all("table", {"class": "prettytable matchrecap2"})
    for team_stat in game.team_stats:
        if team_stat.color == 'blue':
            parse_team_game(game, blue_team, team_stat, game_tables[1])
        elif team_stat.color == 'red':
            parse_team_game(game, red_team, team_stat, game_tables[2])
        else:
            print('problem parsing team does is neither blue not red it is: {}'.format(team_stat.color))
    return game

def parse_game_info(recap_table):
    # should only be 1 info_table
    game = Game()
    game_info_table = recap_table.find("table", {"class": "wikitable matchrecap2"})
    blue_team = parse_team_game_info('blue', game_info_table, game)
    red_team = parse_team_game_info('red', game_info_table, game)
    return blue_team, red_team, game


def parse_team_game_info(color, game_info_table, game):
    # team = {'color': color, 'total_gold': 0, 'team_name': '', 'game_length_minutes': 0, 'won': None}
    team_stats = TeamStats(minions_killed=0, assists=0, deaths=0, kills=0, gold=0)
    session.add(team_stats)
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
    if team_stats.color == 'red':
        team_name = cols[3].contents[0].strip()
        team_name = team_name.upper()
        team = get_or_create(session, Team, external_name=team_name)
        team.name = team_name
        team_stats.total_gold = float(cols_game_stats_info[10].contents[0].strip().replace('k', '')) * 1000
        team_stats.turrets = parse_column_stats(cols_game_stats_info[8])
        team_stats.dragons = parse_column_stats(cols_game_stats_info[7])
        team_stats.barons = parse_column_stats(cols_game_stats_info[6])
        try:
            if cols[2]['style'] == 'background-color:#ccffcc':
                team_stats.won = True
        except KeyError:
            team_stats.won = False
    elif team_stats.color == 'blue':
        team_name = cols[0].contents[0].strip()
        team_name = team_name.upper()
        team = get_or_create(session, Team, external_name=team_name)
        team.name = team_name
        team_stats.total_gold = float(cols_game_stats_info[0].contents[2].strip().replace('k', '')) * 1000
        team_stats.turrets = int(str(cols_game_stats_info[2].contents[2].strip()))
        team_stats.dragons = int(str(cols_game_stats_info[3].contents[2].strip()))
        team_stats.barons = int(str(cols_game_stats_info[4].contents[2].strip()))
        try:
            if cols[1]['style'] == 'background-color:#ccffcc':
                team_stats.won = True
        except KeyError:
            team_stats.won = False
    game.team_stats.append(team_stats)
    team.team_stats.append(team_stats)
    return team


def get_games_from_webpage(web_page=None):
    data_source = session.query(DataSource).filter(DataSource.external_location == web_page).first()
    if data_source is None:
        try:
            retrieved_data_source = DataSource(name='WEB', external_location=web_page)
            retrieved_tournament = get_tournament_from_web_page(web_page)
            retrieved_tournament.data_sources.append(retrieved_data_source)
            session.add(retrieved_data_source)
            response = requests.get(web_page)
            text = response.text
            soup = BeautifulSoup(text)
            retrieved_data_source = process_data_source(soup, retrieved_data_source, retrieved_tournament)
            session.commit()
            print('Webpage {} has been processed'.format(web_page))
        except (exc.SQLAlchemyError, IndexError, ValueError) as e:
            print('There was a problem loading the webpage {} rolling back now'.format(web_page))
            print('The exception is {}'.format(e))
            print('Stacktract {}'.format(traceback.format_exc()))
            session.rollback()
    else:
        print('Webpage {} is already processed'.format(web_page))


def get_games_from_webpages(base_page, pages):
    data_sources = []
    for page in pages:
        web_page = '{}{}'.format(base_page, page)
        data_source = get_games_from_webpage(web_page)
        data_sources.append(data_source)
    return data_sources





def main():
    get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/2015_Season_World_Championship/Scoreboards',
                           pages=['', '/Group_Stage/Group_B', '/Group_Stage/Group_C', '/Group_Stage/Group_D', '/Bracket_Stage'])
    get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/League_Championship_Series/North_America/2016_Season/Spring_Season/Scoreboards',
                           pages=[''])
    get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/League_Championship_Series/Europe/2016_Season/Spring_Season/Scoreboards',
                           pages=[''])
    get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/LCK/2016_Season/Spring_Season/Scoreboards',
                           pages=[''])
    # get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/LPL/2016_Season/Spring_Season/Scoreboards',
    #                        pages=[''])
    get_games_from_webpages(base_page='http://lol.esportspedia.com/wiki/LMS/2016_Season/Spring_Season/Scoreboards',
                           pages=[''])

if __name__ == "__main__":
    main()
