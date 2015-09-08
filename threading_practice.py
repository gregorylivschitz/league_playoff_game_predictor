__author__ = 'glivschitz'

from threading import Thread
import pandas

def do_work(thead_name):
    for i in range(0, 90000):
        print('{} {}'.format(i, thead_name))

thread_a = Thread(name='a', target=do_work('a'))
thread_b = Thread(name='b', target=do_work('b'))
thread_a.start()
thread_b.start()

eu_team_df = pandas.DataFrame({'eff_minions_killed': [1, 2, 3, 4, 5, 6],
                                   'eff_total_gold': [1, 2, 3, 4, 5, 6],
                                   'csum_prev_min_minions_killed': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_total_gold': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_kills': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_deaths': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_assists': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_K_A': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_min_A_over_K': [1, 1, 1, 1, 1, 1],
                                   'csum_prev_kda': [1, 1, 1, 1, 1, 1],
                                   'eff_kills': [1, 1, 1, 1, 1, 1],
                                   'eff_deaths': [1, 1, 1, 1, 1, 1],
                                   'eff_assists': [1, 1, 1, 1, 1, 1],
                                   'eff_K_A': [1, 1, 1, 1, 1, 1],
                                   'eff_A_over_K': [1, 1, 1, 1, 1, 1],
                                   'color': ['red', 'blue', 'red', 'blue', 'red', 'blue'],
                                   'game_id': ['1', '1', '2', '2', '3', '3'],
                                   'won_x': [True, False, False, True, True, False]})
na_team_df = pandas.DataFrame({'eff_minions_killed': [1, 2, 3, 4, 5, 6],
                               'eff_total_gold': [1, 2, 3, 4, 5, 6],
                               'csum_prev_min_minions_killed': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_total_gold': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_kills': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_deaths': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_assists': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_K_A': [1, 1, 1, 1, 1, 1],
                               'csum_prev_min_A_over_K': [1, 1, 1, 1, 1, 1],
                               'csum_prev_kda': [1, 1, 1, 1, 1, 1],
                               'eff_kills': [1, 1, 1, 1, 1, 1],
                               'eff_deaths': [1, 1, 1, 1, 1, 1],
                               'eff_assists': [1, 1, 1, 1, 1, 1],
                               'eff_K_A': [1, 1, 1, 1, 1, 1],
                               'eff_A_over_K': [1, 1, 1, 1, 1, 1],
                               'color': ['red', 'blue', 'red', 'blue', 'red', 'blue'],
                               'game_id': ['1', '1', '2', '2', '3', '3'],
                               'won_x': [True, False, False, True, True, False]})
