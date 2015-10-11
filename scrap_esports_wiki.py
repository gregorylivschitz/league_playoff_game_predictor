__author__ = 'Greg'

from bs4 import BeautifulSoup, NavigableString
import requests
import sys

# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}

response = requests.get('http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards')
text = response.text
soup = BeautifulSoup(text)

# parse recap tables into a list of team tuples
def parse_recap_tables(soup):
    games = []
    games_info = []
    for recap_table in soup.find_all("table", {"class": "wikitable matchrecap1"}):
        games.append(parse_game(recap_table))
        games_info.append(parse_game_info(recap_table))

# given a column, get contents and strip garbage
def parse_column(col):
    # assume col.contents has value we want at index 0
    return int(str(col.contents[0]).strip())

# parse values from table and add to team
def parse_player_stats(team, player_stat_table):
    rows = player_stat_table.find_all("tr")
    # assume len(row) == 1
    row = rows[0]
    cols = row.find_all('td')
    # assume len(cols) == 11
    team['minions_killed'] += parse_column(cols[10])
    team['assists'] += parse_column(cols[6])
    team['deaths'] += parse_column(cols[5])
    team['kills'] += parse_column(cols[4])
    return team

# color, game_table to
# {'color': 'blue', 'assists': 37, 'deaths': 5, 'kills': 16,'minions_killed': 783}
def parse_team_game(color, game_table):
    team = {'color': color, 'assists': 0, 'deaths': 0, 'kills': 0, 'minions_killed': 0}
    player_stats_tables = game_table.find_all("table", {"class": "prettytable"})
    for player_stat_table in player_stats_tables:
        parse_player_stats(team, player_stat_table)
    return team

# list of tables to
# ( {'color': 'blue', 'assists': 37,'deaths': 5, 'kills': 16,'minions_killed': 783}, {'color': 'red', 'assists': 37,
# 'deaths': 5, 'kills': 16, 'minions_killed': 783})
def parse_game(recap_tables):
    # len(game_tables) == 3 assumption
    # game_tables[0] skip
    # game_tables[1] is blue team
    # game_tables[2] is red team
    game_tables = recap_tables.find_all("table", {"class": "prettytable matchrecap2"})
    return parse_team_game('blue', game_tables[1]), parse_team_game('red', game_tables[2])




def parse_game_info(recap_table):
    # should only be 1 info_table
    game_info_table = recap_table.find("table", {"class": "wikitable matchrecap2"})
    return parse_team_game_info('blue', game_info_table), parse_team_game_info('red', game_info_table)


def parse_team_game_info(color, game_info_table):
    team = {'color': color, 'total_gold': 0, 'team_name': '', 'game_length_minutes': 0, 'won': None}
    rows = game_info_table.find_all('tr')
    # row where team name is kept and how we determine the win vs the loss
    row_game_info = rows[1]
    row_game_info

parse_recap_tables(soup)
#
# blue_team = {'color': 'blue'}
# red_team = {'color': 'red'}
# soup_table = soup.find_all("table", {"class": "wikitable matchrecap1"})
# for table in soup_table:
#     recap_tables = table.find_all("table", {"class": "wikitable matchrecap2"})
#     print(recap_tables)
#     sys.exit()
#     # for recap_table in recap_tables:
#     #     print(recap_table)
#     #     sys.exit()
#     #     all_td = []
#     #     rows = recap_table.find_all("tr")
#     #     for index, row in enumerate(rows):
#     #         cols = row.find_all('td')
#     #         # find the correct td and the one with the background color of ccffcc is the team that won.
#     #         if index == 1:
#     #             try:
#     #                 if cols[1]['style'] == 'background-color:#ccffcc':
#     #                     blue_team['won'] = True
#     #                     red_team['won'] = False
#     #             except KeyError:
#     #                 if cols[2]['style'] == 'background-color:#ccffcc':
#     #                     blue_team['won'] = False
#     #                     red_team['won'] = True
#     #         for col in cols:
#     #             if len(col.contents) == 3:
#     #                 if 'div' not in str(col.contents[1]):
#     #                     if col.span['title'] == 'Total Gold':
#     #                         if len(col.contents[0].strip()) == 0:
#     #                             total_gold = float(col.contents[2].string.strip().replace('k', '')) * 1000
#     #                             blue_team['total_gold'] = total_gold
#     #                         if len(col.contents[2].strip()) == 0:
#     #                             total_gold = float(col.contents[0].string.strip().replace('k', '')) * 1000
#     #                             red_team['total_gold'] = total_gold
#     #                     if col.span['title'] == 'Total Kills':
#     #                         if len(col.contents[0].strip()) == 0:
#     #                             kills = int(col.contents[2].string.strip())
#     #                             blue_team['kills'] = kills
#     #                         if len(col.contents[2].strip()) == 0:
#     #                             kills = int(col.contents[0].string.strip())
#     #                             red_team['kills'] = kills
#     #             all_td.append(str(col.contents[0]))
#     #     all_td = list(map(lambda x: x.strip(), all_td))
#     #     all_td = list(filter(lambda x: x.strip(), all_td))
#     #     blue_team['team_name'] = all_td[0]
#     #     red_team['team_name'] = all_td[3]
#     #     game_length_minutes = all_td[7].replace(':', '.')
#     #     blue_team['game_length_minutes'] = game_length_minutes
#     #     red_team['game_length_minutes'] = game_length_minutes
#     #     print(blue_team)
#     #     print(red_team)
#     #
