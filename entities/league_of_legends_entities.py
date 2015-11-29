from sqlalchemy import Column, Table, Integer, ForeignKey, create_engine, String, Boolean, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

__author__ = 'Greg'

engine = create_engine('postgresql://postgres:postgres@localhost:5432/yolobid', echo=True)
Session = sessionmaker(bind=engine)
Base = declarative_base()

game_team = Table('game_team', Base.metadata,
                  Column('game_id', Integer, ForeignKey('game.id')),
                  Column('team_id', Integer, ForeignKey('team.id'))
                  )

team_player = Table('team_player', Base.metadata,
                    Column('team_id', Integer, ForeignKey('team.id')),
                    Column('player_id', Integer, ForeignKey('player.id'))
                    )


class Game(Base):
    """Game object"""
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    teams = relationship('Team', secondary=game_team, backref='games')
    game_length_minutes = Column(Numeric)
    external_id = Column(Integer)
    data_source_id = Column(Integer, ForeignKey('data_source.id'))

    def __str__(self):
        return 'id: {}, teams: {}, game_length: {}, external_id: {}, data_source_id: {}'.format\
            (self.id, self.teams, self.game_length_minutes, self.external_id, self.data_source_id)


class Team(Base):
    """Team object"""
    __tablename__ = 'team'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    external_name = Column(String)
    external_id = Column(Integer)
    team_stats = relationship("TeamStats", backref='team')
    players = relationship('Player', secondary=team_player, backref='teams')

    def __str__(self):
        return 'id: {}, name: {}, external_name: {}, external_id: {}, team_stats: {}, players {}'.format\
            (self.id, self.name, self.external_name, self.external_id, self.team_stats, self.players)


class DataSource(Base):
    """DataSource object"""
    __tablename__ = 'data_source'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    external_location = Column(String)
    games = relationship('Game', backref="datasource")

    def __str__(self):
        return 'id: {}, name: {}, external_location: {}, games: {}'.format\
            (self.id, self.name, self.external_location, self.games)

class Player(Base):
    """Player Object"""
    __tablename__ = 'player'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    player_stats = relationship("PlayerStats", backref='player')


class TeamStats(Base):
    """TeamStats Object"""
    __tablename__ = 'team_stats'
    id = Column(Integer, primary_key=True)
    total_gold = Column(String)
    won = Column(Boolean)
    color = Column(String)
    deaths = Column(Integer)
    minions_killed = Column(Integer)
    assists = Column(Integer)
    kills = Column(Integer)
    gold = Column(Numeric)
    barons = Column(Integer)
    dragons = Column(Integer)
    team_id = Column(Integer, ForeignKey('team.id'))

    def __str__(self):
        return 'won: {}, color: {}'.format(self.won, self.color)


class PlayerStats(Base):
    """PlayerStats Object"""
    __tablename__ = 'player_stats'
    id = Column(Integer, primary_key=True)
    kills = Column(Integer)
    deaths = Column(Integer)
    assists = Column(Integer)
    gold = Column(Numeric)
    minions_killed = Column(Integer)
    player_id = Column(Integer, ForeignKey('player.id'))


Base.metadata.create_all(engine)
# print(Base.metadata.sorted_tables)
# for tbl in reversed(Base.metadata.sorted_tables):
#     print(tbl)
#     engine.execute(tbl.drop())
