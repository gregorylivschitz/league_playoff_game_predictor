from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from predict_team_outcome import PredictTeamWin
__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=False)
Session = sessionmaker(bind=engine)
session = Session()
predict = PredictTeamWin(session, engine,  'Counter Logic Gaming', 'SKTelecom T1')
print(predict.predict_on_single_game())
predict = PredictTeamWin(session, engine,  'SKTelecom T1', 'Counter Logic Gaming')
print(predict.predict_on_single_game())
# print(predict.predict_multiple_game_series()