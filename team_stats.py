__author__ = 'Greg'


class TeamStats:
    """Team stats for league of legends"""

    def __init__(self, team_id, kda, kills, deaths, assits, minions_killed, total_gold, gpm):
        self.team_id = team_id
        self.kda = kda
        self.kills = kills
        self.deaths = deaths
        self.assits = assits
        self.minions_killed = minions_killed
        self.total_gold = total_gold
        self.gpm = gpm
