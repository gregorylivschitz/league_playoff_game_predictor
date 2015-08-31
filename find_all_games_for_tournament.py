import json
import requests

__author__ = 'Greg'

def get_all_games_for_one_tournament(tournament):
    games_in_tourney = []
    for game_id in range(7000, 7090):
        response = requests.get('http://na.lolesports.com:80/api/game/{}.json'.format(game_id))
        game_league = response.text
        j_game_league = json.loads(game_league)
        print('on game_id: {}'.format(game_id))
        if j_game_league != ['Entity not found']:
            if j_game_league['tournament']['id'] == tournament:
                print('found {} for tournament {}'.format(game_id, tournament))
                games_in_tourney.append(game_id)
    print(games_in_tourney)
    return games_in_tourney


def main():
    # eu playoffs [7061, 7062, 7063, 7064, 7065, 7066]
    # na playoffs [7067, 7068, 7069, 7070, 7071, 7072]
    get_all_games_for_one_tournament('240')

if __name__ == "__main__":
    main()