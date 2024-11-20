import numpy as np
import pandas as pd
from pbp_utils import get_starters_of_game
from plots_utils import plot_plusminus_heatmap_seaborn, plot_heatmap_seaborn, plot_game_diff_seaborn, all_plots_game


def find_missing(indices):
    missing_ranges = []
    start = None
    for i in range(indices[0], indices[-1]):
        if i not in indices:
            if start is None:
                start = i
        elif start is not None:
            missing_ranges.append((start, i-1))
            start = None
    if start is not None:
        missing_ranges.append((start, indices[-1]))
    return missing_ranges


def get_first_last_time(player_df, player_df_filtered, quarter):
    # Get the first and last row of the player dataframe
    first_row = player_df_filtered.iloc[0]
    last_row = player_df_filtered.iloc[-1]

    # Extract the time information from the first and last row
    first_time = first_row['Time']
    last_time = last_row['Time']

    # Extract the minutes from the time strings
    first_minute = int(first_time.split(':')[0])
    last_minute = int(last_time.split(':')[0])

    if first_minute == 9 and \
        player_df.iloc[0]['Unnamed: 0'] == player_df_filtered.iloc[0]['Unnamed: 0'] and \
        'Substitution' not in player_df_filtered.iloc[0].Action_Description:

        first_minute = 10
        first_time = '10:00'

    return first_minute, last_minute, first_time, last_time

def compute_difference(heatmap_dict, player_number, first_minute, last_minute, first_time, last_time):
    # Compute the time difference
    if first_minute == last_minute:
        percentage_played = (int(first_time.split(':')[1]) - int(last_time.split(':')[1]))/60
        if heatmap_dict[player_number].get(f'{first_minute+1}-{first_minute}') ==0 or heatmap_dict[player_number].get(f'{first_minute+1}-{first_minute}') == 1:
            heatmap_dict[player_number][f'{first_minute+1}-{first_minute}'] = percentage_played
        else:
            heatmap_dict[player_number][f'{first_minute+1}-{first_minute}'] += percentage_played
        
    else:
        if first_minute != 10:
            first_minute = first_minute+1
        for i in range(first_minute, last_minute-1, -1):
            if i not in [first_minute, last_minute]:
                heatmap_dict[player_number][f'{i}-{i-1}'] = 1
            else:
                if i == first_minute:
                    if int(first_time.split(':')[1]) == 0:
                        percentage_played = 1
                        if i != 10:
                            heatmap_dict[player_number][f'{i-1}-{i-2}'] = percentage_played
                        else:
                            heatmap_dict[player_number][f'{i}-{i-1}'] = percentage_played
                    else:
                        percentage_played = int(first_time.split(':')[1])/60
                        if heatmap_dict[player_number].get(f'{i}-{i-1}') ==0 or heatmap_dict[player_number].get(f'{i}-{i-1}') == 1:
                            heatmap_dict[player_number][f'{i}-{i-1}'] = percentage_played
                        else:
                            heatmap_dict[player_number][f'{i}-{i-1}'] += percentage_played

                elif i == last_minute:
                    percentage_played = (60 - int(last_time.split(':')[1]))/60
                    if heatmap_dict[player_number].get(f'{i+1}-{i}') ==0 or heatmap_dict[player_number].get(f'{i+1}-{i}') == 1:
                        heatmap_dict[player_number][f'{i+1}-{i}'] = percentage_played
                    else:
                        heatmap_dict[player_number][f'{i+1}-{i}'] += percentage_played
                    break

    return heatmap_dict

def player_time_percentage(heatmap_dict, all_pbp, player_number, team_str, quarter):
    
    heatmap_dict[player_number] = {}
    # Filter the dataframe for the specified player and team
    player_df = all_pbp[(all_pbp['X_' + str(player_number) + '_j_' + team_str] == 1)&(all_pbp.quarter == quarter)]

    for i in range(10, 0, -1): 
        heatmap_dict[player_number][f'{i}-{i-1}'] = 0

        
    if len(player_df) > 0:
        # Create a boolean Series where True indicates a break in the sequence
        breaks = player_df.index.to_series().diff() != 1

        # Use groupby to find the start and end of each continuous sequence
        player_df['Unnamed: 0'] = player_df.index
        intervals = player_df.groupby(breaks.cumsum()).agg({'Unnamed: 0': ['min', 'max']})

        # Iterate over the intervals and compute the time difference
        for interval in intervals.itertuples(index=False):
            start, end = interval
            player_df_filtered = player_df.loc[start:end]
            first_minute, last_minute, first_time, last_time = get_first_last_time(player_df, player_df_filtered, quarter)
            if first_time != last_time:
                heatmap_dict = compute_difference(heatmap_dict, player_number, first_minute, last_minute, first_time, last_time)

    return heatmap_dict





def get_heatmap_dicts_df(all_pbp, team_str, team_name, dict_players_numbers):
    heatmap_dict1 = {}
    heatmap_dict2 = {}
    heatmap_dict3 = {}
    heatmap_dict4 = {}

    for player_number in all_pbp[all_pbp['Team'] == team_name]['Number'].unique():
        if not np.isnan(player_number):
            heatmap_dict1 = player_time_percentage(heatmap_dict1, all_pbp, int(player_number), team_str, 1)
            heatmap_dict2 = player_time_percentage(heatmap_dict2, all_pbp, int(player_number), team_str, 2)
            heatmap_dict3 = player_time_percentage(heatmap_dict3, all_pbp, int(player_number), team_str, 3)
            heatmap_dict4 = player_time_percentage(heatmap_dict4, all_pbp, int(player_number), team_str, 4)

    time_percentages_df1 = pd.DataFrame(heatmap_dict1).T.fillna(0)
    time_percentages_df2 = pd.DataFrame(heatmap_dict2).T.fillna(0)
    time_percentages_df3 = pd.DataFrame(heatmap_dict3).T.fillna(0)
    time_percentages_df4 = pd.DataFrame(heatmap_dict4).T.fillna(0)

    assert np.all(np.isclose(time_percentages_df1.sum(), 5.0))
    assert np.all(np.isclose(time_percentages_df2.sum(), 5.0))
    assert np.all(np.isclose(time_percentages_df3.sum(), 5.0))
    assert np.all(np.isclose(time_percentages_df4.sum(), 5.0))

    time_percentages_df1 = time_percentages_df1.reset_index(names='name_player')
    time_percentages_df1['name_player'] = time_percentages_df1['name_player'].apply(lambda x: dict_players_numbers[x])
    time_percentages_df1.set_index('name_player', inplace=True)

    time_percentages_df2 = time_percentages_df2.reset_index(names='name_player')
    time_percentages_df2['name_player'] = time_percentages_df2['name_player'].apply(lambda x: dict_players_numbers[x])
    time_percentages_df2.set_index('name_player', inplace=True)

    time_percentages_df3 = time_percentages_df3.reset_index(names='name_player')
    time_percentages_df3['name_player'] = time_percentages_df3['name_player'].apply(lambda x: dict_players_numbers[x])
    time_percentages_df3.set_index('name_player', inplace=True)

    time_percentages_df4 = time_percentages_df4.reset_index(names='name_player')
    time_percentages_df4['name_player'] = time_percentages_df4['name_player'].apply(lambda x: dict_players_numbers[x])
    time_percentages_df4.set_index('name_player', inplace=True)
    return time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4


def get_dict_players_numbers(all_pbp, team1):
    unique_number_name = all_pbp[(all_pbp.Team == team1)&(~all_pbp.Number.isnull())][['Number', 'Player']].drop_duplicates()
    dict_players_numbers  = dict(zip(unique_number_name['Number'], unique_number_name['Player']))
    return dict_players_numbers


def compute_new_columns_and_dfs(all_pbp, team_str):
    all_pbp_no_end_q = all_pbp[(all_pbp.Action_Description!='End of quarter')].copy()
    all_pbp_no_end_q['minute'] = all_pbp_no_end_q['Time'].apply(lambda x: int(x.split(':')[0]))
    all_pbp_no_end_q.loc[all_pbp_no_end_q.minute==10, 'minute'] = 9
    if team_str == 'A':
        all_pbp_no_end_q['diferential_past_row'] = all_pbp_no_end_q['Score_A'].shift() - all_pbp_no_end_q['Score_B'].shift()
        all_pbp_no_end_q.loc[all_pbp_no_end_q.index[0], 'diferential_past_row'] = 0
        all_pbp_no_end_q['+/-'] = all_pbp_no_end_q['Score_A'] - all_pbp_no_end_q['Score_B']
        heatmap_plus_minus = all_pbp_no_end_q.groupby(['quarter','minute']).apply(lambda x: (x['Score_A'].iloc[-1] - x['Score_B'].iloc[-1])-(x['diferential_past_row'].iloc[0])).reset_index()
    elif team_str == 'B':
        all_pbp_no_end_q['diferential_past_row'] = all_pbp_no_end_q['Score_B'].shift() - all_pbp_no_end_q['Score_A'].shift()
        all_pbp_no_end_q.loc[all_pbp_no_end_q.index[0], 'diferential_past_row'] = 0
        all_pbp_no_end_q['+/-'] = all_pbp_no_end_q['Score_B'] - all_pbp_no_end_q['Score_A']
        heatmap_plus_minus = all_pbp_no_end_q.groupby(['quarter','minute']).apply(lambda x: (x['Score_B'].iloc[-1] - x['Score_A'].iloc[-1])-(x['diferential_past_row'].iloc[0])).reset_index()

    heatmap_plus_minus = heatmap_plus_minus.rename(columns={0: 'plusminus'})
    return all_pbp_no_end_q, heatmap_plus_minus

def final_plot_for_team(url, all_pbp, team1, team_str):
    assert team_str in ['A', 'B']
    dict_players_numbers  =  get_dict_players_numbers(all_pbp, team1)
    time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4 = get_heatmap_dicts_df(all_pbp, team_str, team1, dict_players_numbers)
    # starters_A, starters_B, boxscore_A, boxscore_B = get_starters_of_game(url)
    # players_order_A = starters_A + [p for p in boxscore_A.sort_values('Min', ascending=False).Players.tolist() if p not in starters_A and p not in ['Totals', 'Team/Coaches']]
    # players_order_B = starters_B + [p for p in boxscore_B.sort_values('Min', ascending=False).Players.tolist() if p not in starters_B and p not in ['Totals', 'Team/Coaches']]
    
    all_pbp_no_end_q, heatmap_plus_minus = compute_new_columns_and_dfs(all_pbp, team_str)
    teams = url.split('/')[-1].split('-')
    if len(teams) >2:
        teams = teams[1:]
    scores = (all_pbp_no_end_q['Score_A'].max(), all_pbp_no_end_q['Score_B'].max())
    all_plots_game(time_percentages_df1, time_percentages_df2, time_percentages_df3, time_percentages_df4, heatmap_plus_minus, all_pbp_no_end_q, teams, scores)
