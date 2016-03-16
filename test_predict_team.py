from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from predict_player_stats import PredictPlayerStats
from predict_team_outcome import PredictTeamWin
__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=False)
# predict = PredictTeamWin(engine,  'Counter Logic Gaming', 'SKTelecom T1')
# print(predict.predict_on_single_game())
# predict = PredictTeamWin(engine,  'BANGKOK TITANS', 'COUNTER LOGIC GAMING', predictor_stats=('csum_prev_min_a_over_k',))
# print(predict.predict_on_single_game())


predict_player = PredictPlayerStats(engine, 'Doublelift', 'gold')
print(predict_player.predict_player_stat())
