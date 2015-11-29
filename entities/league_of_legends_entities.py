from sqlalchemy import Column, Table, Integer, ForeignKey, create_engine, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

games_team = Table('games_teams', Base.metadata,
                   Column('game_id', Integer, ForeignKey('games.id')),
                   Column('team_id', Integer, ForeignKey('teams.id'))
                   )


class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    teams = relationship("Team", secondary=games_team)


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    external_name = Column(String)


Base.metadata.create_all(engine)