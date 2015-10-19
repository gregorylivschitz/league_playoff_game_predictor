__author__ = 'Greg'

from bs4 import BeautifulSoup, NavigableString
import requests

# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}

# # Things we need real_name instead of team_name, team_id, game_id
# [({'total_gold': 48300.0, 'won': False, 'color': 'blue', 'game_length_minutes': '33.32', 'deaths': 9, 'minions_killed': 952, 'assists': 11, 'team_name': 'Team WE', 'kills': 6},
# {'total_gold': 48300.0, 'won': True, 'color': 'red', 'game_length_minutes': '33.32', 'deaths': 6, 'minions_killed': 1089, 'assists': 29, 'team_name': 'Invictus Gaming', 'kills': 9})

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
    team['game_number'] = 1
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
    rows_game_stats_info = rows[3]
    cols_game_stats_info = rows_game_stats_info.find_all('td')
    team['game_length_minutes'] = float(cols_game_stats_info[5].contents[0].strip().replace(':', '.').replace('!', '1'))
    # cols[0] = blue team_name, cols[1] = blue win or loss, cols[3] = red team name, cols[2] = red won or losee
    if team['color'] == 'blue':
        team['team_name'] = cols[0].contents[0].strip()
        team['total_gold'] = float(cols_game_stats_info[10].contents[0].strip().replace('k', '')) * 1000
        try:
            if cols[1]['style'] == 'background-color:#ccffcc':
                team['won'] = True
        except KeyError:
            team['won'] = False
    elif team['color'] == 'red':
        team['team_name'] = cols[3].contents[0].strip()
        team['total_gold'] = float(cols_game_stats_info[0].contents[2].strip().replace('k', '')) * 1000
        try:
            if cols[2]['style'] == 'background-color:#ccffcc':
                team['won'] = True
        except KeyError:
            team['won'] = False
    return team


def get_all_web_pages(web_page, pages, game_ids, team_name_ids):
    all_merge_games = []
    for page in range(1, pages + 1):
        if page == 1:
            response = requests.get(web_page)
        else:
            web_page_week_n = '{}/Week_{}'.format(web_page, page)
            response = requests.get(web_page_week_n)
        text = response.text
        soup = BeautifulSoup(text)
        merge_games = merge_game_and_game_info(soup)
        all_merge_games += merge_games
    assign_game_id_and_team_id(all_merge_games, game_ids, team_name_ids)
    return all_merge_games


def assign_game_id_and_team_id(all_merge_games, game_ids, team_name_ids):
    for index, merge_game in enumerate(all_merge_games):
        blue_team, red_team = merge_game
        red_team['game_id'] = game_ids[index]
        blue_team['game_id'] = game_ids[index]
        red_team['team_id'] = team_name_ids[red_team['team_name']]
        blue_team['team_id'] = team_name_ids[blue_team['team_name']]
        all_merge_games[index] = (red_team, blue_team)
    return all_merge_games


def get_games_from_webpage(game_ids):
    lpl_team_id_mapping = {'Oh My God': 10000, 'Unlimited Potential': 10001, 'Masters 3': 10002, 'Vici Gaming': 10003,
                           'Royal Never Give Up': 10004, 'Team WE': 10005, 'EDward Gaming': 10006, 'LGD Gaming': 10007,
                           'Team King': 10008, 'Invictus Gaming': 10009, 'Qiao Gu Reapers': 10010,
                           'Snake eSports': 10011}
    pages = 11
    web_page = 'http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards'
    print(get_all_web_pages(web_page, pages, game_ids, lpl_team_id_mapping))
    return get_all_web_pages(web_page, pages, game_ids, lpl_team_id_mapping)


def main():
    lpl_games = [6539, 6540, 6541, 6542, 6543, 6544, 6545, 6546, 6547, 6548, 6549, 6550, 6551, 6552, 6553,
                 6554, 6555, 6556, 6557, 6558, 6559, 6560, 6561, 6562, 6563, 6564, 6565, 6566, 6567, 6568, 6569, 6570,
                 6571, 6572, 6573, 6574, 6575, 6576, 6577, 6578, 6579, 6580, 6581, 6582, 6583, 6584, 6585, 6586, 6587,
                 6588, 6589, 6590, 6591, 6592, 6593, 6594, 6595, 6596, 6597, 6598, 6599, 6600, 6601, 6602, 6603, 6604,
                 6605, 6606, 6607, 6612, 6613, 6614, 6615, 6620, 6621, 6622, 6623, 6627, 6628, 6629, 6630, 6718, 6719,
                 6720, 6721, 6724, 6725, 6726, 6727, 6732, 6733, 6734, 6735, 6753, 6754, 6755, 6756, 6768, 6769, 6770,
                 6771, 6772, 6773, 6774, 6775, 6826, 6827, 6828, 6829, 6830, 6831, 6838, 6839, 6844, 6845, 6846, 6847,
                 6947, 6948, 6949, 6950, 6958, 6959, 6960, 6961, 6968, 6969, 6970, 6971, 7028, 7029, 7030, 7031, 7041,
                 7044, 7045, 7047, 7050, 7051, 7052, 7053, 7073, 7074, 7075, 7080, 7083, 7084, 7085, 7089, 7091, 7092,
                 7093, 7094, 7134, 7135, 7136, 7137, 7138, 7139, 7140, 7143, 7147, 7148, 7149, 7150, 7164, 7165, 7168,
                 7172, 7174, 7177, 7184, 7187, 7188, 7189, 7192, 7193, 7210, 7211, 7212, 7213, 7216, 7217, 7218, 7219,
                 7223, 7224, 7225, 7226, 7241, 7242, 7243, 7244, 7248, 7249, 7253, 7255, 7260, 7261, 7262, 7263, 7285,
                 7286, 7287, 7288, 7289, 7290, 7291, 7292, 7293, 7294, 7295, 7296, 7297, 7298, 7299, 7300, 7301, 7302,
                 7303, 7304, 7305, 7306, 7307, 7308, 7309, 7310, 7311, 7312, 7313, 7315, 7316, 7324, 7325, 7328, 7329,
                 7330, 7331, 7332, 7352, 7353, 7354, 7355, 7356, 7381, 7382, 7383, 7384, 7385, 7386, 7387, 7392, 7395,
                 7396, 7397, 7398, 7399, 7409, 7410, 7411, 7444, 7445, 7446, 7447]
    get_games_from_webpage(lpl_games)


if __name__ == "__main__":
    main()
