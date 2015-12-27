from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from predict_team_outcome import PredictTeamWin
__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=False)
Session = sessionmaker(bind=engine)
session = Session()
predict = PredictTeamWin(session, engine, 'CLG', 'TSM')
predict.predict_on_model()