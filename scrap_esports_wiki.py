__author__ = 'Greg'

from bs4 import BeautifulSoup
import requests
import sys


# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16,
# 'minions_killed': 783}




response = requests.get('http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards')
text = response.text
soup = BeautifulSoup(text)
soup_tables = soup.find_all("table", {"class": "wikitable matchrecap1"})
all_td = []
for table in soup_tables:
    recap_tables = table.find_all("table", {"class": "prettytable matchrecap2"})
    for recap_table in recap_tables:
        player_stats = recap_table.find_all("table", {"class": "prettytable"})
        for player_stat in player_stats:
            all_td = []
            rows = player_stat.find_all("tr")
            for index, row in  enumerate(rows):
                cols = row.find_all('td')
                # Get player name
                # print(cols[1].a['title'])
                for col in cols:
                    # print(col.contents)
                    all_td.append(str(col.contents[0]))
            all_td = list(map(lambda x: x.strip(), all_td))
            all_td = list(filter(lambda x: x.strip(), all_td))
            # 9 = cs, 5 = assists, 4 = deaths, 3 = kills,
            # print(all_td[0])
            sys.exit()

            # for index, row in enumerate(rows):
            #     cols = row.find_all('td')
            #     for col in cols:
            #         # print(col)
            #         all_td.append(str(col.contents))
            # all_td = list(map(lambda x: x.strip(), all_td))
            # all_td = list(filter(lambda x: x.strip(), all_td))
            # # print(all_td)

            # break














# blue_team = {'color': 'blue'}
# red_team = {'color': 'red'}
# for table in soup_tables:
#     recap_tables = table.find_all("table", {"class": "wikitable matchrecap2"})
#     for recap_table in recap_tables:
#         all_td = []
#         rows = recap_table.find_all("tr")
#         for index, row in enumerate(rows):
#             cols = row.find_all('td')
#             # find the correct td and the one with the background color of ccffcc is the team that won.
#             if index == 1:
#                 try:
#                     if cols[1]['style'] == 'background-color:#ccffcc':
#                         blue_team['won'] = True
#                         red_team['won'] = False
#                 except KeyError:
#                     if cols[2]['style'] == 'background-color:#ccffcc':
#                         blue_team['won'] = False
#                         red_team['won'] = True
#             for col in cols:
#                 if len(col.contents) == 3:
#                     if 'div' not in str(col.contents[1]):
#                         if col.span['title'] == 'Total Gold':
#                             if len(col.contents[0].strip()) == 0:
#                                 total_gold = float(col.contents[2].string.strip().replace('k', '')) * 1000
#                                 blue_team['total_gold'] = total_gold
#                             if len(col.contents[2].strip()) == 0:
#                                 total_gold = float(col.contents[0].string.strip().replace('k', '')) * 1000
#                                 red_team['total_gold'] = total_gold
#                         if col.span['title'] == 'Total Kills':
#                             if len(col.contents[0].strip()) == 0:
#                                 kills = int(col.contents[2].string.strip())
#                                 blue_team['kills'] = kills
#                             if len(col.contents[2].strip()) == 0:
#                                 kills = int(col.contents[0].string.strip())
#                                 red_team['kills'] = kills
#                 all_td.append(str(col.contents[0]))
#         all_td = list(map(lambda x: x.strip(), all_td))
#         all_td = list(filter(lambda x: x.strip(), all_td))
#         blue_team['team_name'] = all_td[0]
#         red_team['team_name'] = all_td[3]
#         game_length_minutes = all_td[7].replace(':', '.')
#         blue_team['game_length_minutes'] = game_length_minutes
#         red_team['game_length_minutes'] = game_length_minutes
#         print(blue_team)
#         print(red_team)

