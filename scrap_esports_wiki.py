__author__ = 'Greg'

from bs4 import BeautifulSoup, NavigableString
import requests

# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}


def merge_game_and_game_info(soup):
    games, games_info = parse_recap_tables(soup)
    if len(games) != len(games_info):
        raise ValueError('merging error games and games_info did not match something is wrong with the html')
    games_merge = []
    for game_index, game in enumerate(games):
        game_blue_team, game_red_team = game
        game_info_blue_team, game_info_red_team = games_info[game_index]
        game_blue_merged = dict(list(game_blue_team.items()) + list(game_info_blue_team.items()))
        game_red_merged = dict(list(game_red_team.items()) + list(game_info_red_team.items()))
        games_merge.append((game_blue_merged, game_red_merged))
    print(games_merge)
    return games_merge

# parse recap tables into a list of team tuples
def parse_recap_tables(soup):
    games = []
    games_info = []
    for recap_table in soup.find_all("table", {"class": "wikitable matchrecap1"}):
        games.append(parse_game(recap_table))
        games_info.append(parse_game_info(recap_table))
    return games, games_info

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
    cols = row_game_info.find_all('td')
    # cols[0] = blue team_name, cols[1] = blue win or loss, cols[3] = red team name, cols[2] = red won or losee
    if team['color'] == 'blue':
        team['team_name'] = cols[0].contents[0].strip()
        try:
            if cols[1]['style'] == 'background-color:#ccffcc':
                team['won'] = True
        except KeyError:
            team['won'] = False
    elif team['color'] == 'red':
        team['team_name'] = cols[3].contents[0].strip()
        try:
            if cols[2]['style'] == 'background-color:#ccffcc':
                team['won'] = True
        except KeyError:
            team['won'] = False
    rows_game_stats_info = rows[3]
    cols_game_stats_info = rows_game_stats_info.find_all('td')
    team['game_length_minutes'] = cols_game_stats_info[5].contents[0].strip().replace(':', '.')
    team['total_gold'] = float(cols_game_stats_info[0].contents[2].strip().replace('k', '')) * 1000
    return team


def main():
    response = requests.get('http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards')
    text = response.text
    soup = BeautifulSoup(text)
    merge_game_and_game_info(soup)

if __name__ == "__main__":
    main()
