__author__ = 'Greg'

from bs4 import BeautifulSoup
import requests

# Need to get it to look like this:
# {'color': 'blue', 'won': True, 'assists': 37, 'game_number': 1, 'team_name': 'H2K', 'total_gold': 51230,
# 'team_id': 1273, 'game_id': 6092, 'deaths': 5, 'game_length_minutes': 27.816666666666666, 'kills': 16, 'minions_killed': 783}




response = requests.get('http://lol.esportspedia.com/wiki/2015_LPL/Summer/Regular_Season/Scoreboards')
text = response.text
soup = BeautifulSoup(text)


soup_tables = soup.find_all("table", {"class": "wikitable matchrecap1"})
# soup_stuff = soup_tables.find_all("table", {"class": "wikitable matchrecap2"})
# print(soup_stuff)
all_td = []
for table in soup_tables:
    recap_tables = table.find_all("table", {"class": "wikitable matchrecap2"})
    for recap_table in recap_tables:
        for row in recap_table.find_all("tr"):
            cols = row.find_all('td')
            for col in cols:
                all_td.append(str(col.contents[0]))
    all_td = list(map(lambda x: x.strip(), all_td))
    all_td = list(filter(lambda x: x.strip(), all_td))
    print(all_td)
    break
