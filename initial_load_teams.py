from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import entities.league_of_legends_entities as lole

__author__ = 'Greg'

team_id_mappings = {'LGD Gaming': 10007,
                   'KOO Tigers': 3641,
                   'Midnight Sun e-Sports': 3679,
                   'Oh My God': 10000,
                   'Gambit Gaming': 69,
                   'Invictus Gaming': 10009,
                   'Ever': 4989,
                   'paiN Gaming': 583,
                   'SBENU SONICBOOM': 4327,
                   'Machi': 2643,
                   'Masters 3': 10002,
                   'Team King': 10008,
                   'Team Impulse': 3657,
                   'Longzhu Incredible Miracle': 889,
                   'Origen': 3862,
                   'H2K': 1273,
                   'Xenics Storm': 1010,
                   'Dark Wolves': 4987,
                   'Reason Gaming': 1274,
                   'Team Liquid': 3654,
                   'Winners': 4326,
                   'Mousesports': 252,
                   'Team SoloMid': 1,
                   'Rebels Anarchy': 4325,
                   'Team Imagine': 4420,
                   'Samsung Galaxy': 3642,
                   'Snake eSports': 10011,
                   'Royal Never Give Up': 10004,
                   'Kaos Latin Gamers': 4876,
                   'Gamers2': 4035,
                   'Flash Wolves': 1694,
                   'Vici Gaming': 10003,
                   'SK Gaming': 67,
                   'Copenhagen Wolves Academy': 3865,
                   'Team Coast': 5,
                   'Team WE': 10005,
                   'Giants Gaming': 71,
                   'Jin Air Green Wings': 998,
                   'Enemy Esports': 3494,
                   'Cloud9': 304,
                   'NaJin e-mFire': 895,
                   'Counter Logic Gaming': 2,
                   'KT Rolster': 642,
                   'ROCCAT': 1242,
                   'Elements': 3659,
                   'Winterfox': 3658,
                   'SKTelecom T1': 684,
                   'Detonation FocusMe': 4875,
                   'Unlimited Potential': 10001,
                   'Gravity': 3656,
                   'CJ ENTUS': 640,
                   'EDward Gaming': 10006,
                   'Dark Passage': 585,
                   'Bangkok Titans': 1024,
                   'Chiefs eSports Club': 4874,
                   'Team 8': 1258,
                   'Qiao Gu Reapers': 10010,
                   'Hard Random': 4873,
                   'Fnatic': 68,
                   'Team Dignitas': 3,
                   'Copenhagen Wolves': 1100,
                   'Taipei Assassins': 974,
                   'Assassin Sniper': 4360,
                   'Team Dragon Knights': 3856,
                   'Logitech G Sniper': 3677,
                   'ahq e-Sports Club': 949,
                   'Unicorns of Love': 1281,
                   'HongKong Esports': 3680,
                   'Team Fusion': 3495}
team_external_mappings = {'H2K': 'H2k-Gaming', 'SKTelecom T1': 'SK Telecom T1'}


engine = create_engine('postgresql://postgres:postgres@localhost:5432/test_entities', echo=True)
Session = sessionmaker(bind=engine)


def insert_teams():
    session = Session()
    for name, id in team_id_mappings.items():
        if name in team_external_mappings:
            team = lole.Team(name=name.upper(), external_name=team_external_mappings[name].upper(), external_id=id)
        else:
            team = lole.Team(name=name.upper(), external_name=name.upper(), external_id=id)
        session.add(team)
    session.commit()

if __name__ == '__main__':
    insert_teams()



