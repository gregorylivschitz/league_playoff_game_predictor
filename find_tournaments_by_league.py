import json
from requests import HTTPError
import requests
import find_all_games_for_tournament

__author__ = 'Greg'


def find_tournament_by_name_and_ids(name, tournament_ids):
    tournaments = []
    for tournament_id in tournament_ids:
        response = requests.get('http://na.lolesports.com:80/api/tournament/{}.json'.format(tournament_id))
        try:
            response.raise_for_status()
            tournament = response.text
            j_tournament = json.loads(tournament)
            tournament_name = j_tournament['name']
            if name.lower() in tournament_name.lower():
                # print('Found tournamen with {} in it, the tournament is {} and the id is {}'
                #       .format(name, tournament_name, tournament_id))
                tournaments.append(tournament_id)
        except HTTPError:
            print("http errp on tournament_id {}".format(tournament_id))
    print(tournaments)
    games_in_tournaments = find_all_games_for_tournament.get_all_games_for_tournaments(tournaments)
    games_in_tournaments.sort()
    print(games_in_tournaments)
    return games_in_tournaments
if __name__ == "__main__":
    # find_tournament_by_name_and_ids('lck', list(range(205, 260)))
    # find_tournament_by_name_and_ids('lpl', list(range(205, 260)))
    # find_tournament_by_name_and_ids('lms', list(range(205, 260)))
    find_tournament_by_name_and_ids('iwc', list(range(205, 260)))
    # find_tournament_by_name_and_ids('lcs', list(range(205, 260)))