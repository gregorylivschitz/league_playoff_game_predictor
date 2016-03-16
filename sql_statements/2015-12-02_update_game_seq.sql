ALTER SEQUENCE game_id_seq RESTART WITH 9000;
--drop table tournament;
--drop table data_source;
--drop table game;
--drop table team;
--drop table player;
--drop table team_stats;
--drop table player_stats;
--drop table team_player;
--drop table processed_team_stats_df;
--drop table processed_player_stats_df;
--drop table team_stats_df;
--drop table player_stats_df;


update player
set role = 'AD'
where name='LilV';

update player
set role = 'Top'
where name in ('Julian', 'Steve', 'Solo', 'Steak');

update player
set role = 'Jungler'
where name='Moon';
