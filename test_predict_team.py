from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from predict_player_stats import PredictPlayerStats
from predict_team_outcome import PredictTeamWin
__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=False)
predict = PredictTeamWin(engine,  'Counter Logic Gaming', 'SKTelecom T1')
print(predict.predict_on_single_game())
# predict = PredictTeamWin(engine,  'SKTelecom T1', 'Counter Logic Gaming')
# print(predict.predict_on_single_game())
# # print(predict.predict_multiple_game_series()

#
# predict_player = PredictPlayerStats(engine, 'Doublelift')
