import pandas as pd


def get_stats_from_actions(player_stats):
    # Create columns for different boxscore statistics
    boxscore_columns = ['DReb', 'OReb', 'Block', 'Steal', 'Assist', '2FGMissed', '2FGMade', '3FGMissed', '3FGMade', 'FTMissed', 'FTMade', 'Turnover', 'CommittedFouls', 'DrawnFouls']


    boxscore_df = pd.DataFrame(columns=['rsc','Player', 'Nationality'] + boxscore_columns)

    # Iterate over unique players
    for game in player_stats.rsc.unique().tolist():
        for player in player_stats[player_stats.rsc==game]['name'].unique():
            # Initialize counters for each player
            stats_counters = {'2FGMissed': 0, '2FGMade': 0, 'Turnover': 0, 'DrawnFouls': 0, 'DReb':0, 'OReb':0, 'Block':0, 'Steal':0, 'Assist':0, '2FGMissed':0, '2FGMade':0, '3FGMissed':0, '3FGMade':0, 'FTMissed':0, 'FTMade':0, 'Turnover':0, 'CommittedFouls':0, 'DrawnFouls':0}

            # Count actions based on rules
            for index, row in player_stats[(player_stats.name==player)&(player_stats.rsc==game)].iterrows():
                nation = row['Nationality']
                if 'Defensive rebound' in row['Action']:
                    stats_counters['DReb'] += row['count']
                elif 'Offensive rebound' in row['Action']:
                    stats_counters['OReb'] += row['count']
                elif 'Blocked shot' in row['Action']:
                    stats_counters['Block'] += row['count']
                elif 'Steal' in row['Action']:
                    stats_counters['Steal'] += row['count']
                elif 'Assist' in row['Action']:
                    stats_counters['Assist'] += row['count']
                elif 'Free Throw' in row['Action'] and 'missed' in row['Action']:
                    stats_counters['FTMissed'] += row['count']
                elif 'Free Throw' in row['Action'] and 'made' in row['Action']:
                    stats_counters['FTMade'] += row['count']
                elif '3PtsFG' in row['Action'] and 'missed' in row['Action']:
                    stats_counters['3FGMissed'] += row['count']
                elif '3PtsFG' in row['Action'] and 'made' in row['Action']:
                    stats_counters['3FGMade'] += row['count']
                elif '2PtsFG' in row['Action'] and 'missed' in row['Action']:
                    stats_counters['2FGMissed'] += row['count']
                elif '2PtsFG' in row['Action'] and 'made' in row['Action']:
                    stats_counters['2FGMade'] += row['count']
                elif 'Turnover' in row['Action']:
                    stats_counters['Turnover'] += row['count']
                elif 'Foul drawn' in row['Action']:
                    stats_counters['DrawnFouls'] += row['count']
                elif 'Personal foul' in row['Action']:
                    stats_counters['CommittedFouls'] += row['count']

            # Append player's boxscore to the boxscore DataFrame
            boxscore_df = pd.concat([boxscore_df, pd.DataFrame([{'rsc':game, 'Player': player, 'Nationality':nation, **stats_counters}])])
    return boxscore_df

def add_columns(boxscore_df):
    # Add new columns with percentages and advanced statistics
    boxscore_df['FTAttempts'] = boxscore_df['FTMade'] + boxscore_df['FTMissed']
    boxscore_df['FT%'] = round(boxscore_df.apply(lambda x: (x['FTMade'] / x['FTAttempts'] * 100) if x['FTAttempts'] != 0 else 0, axis=1),2)

    boxscore_df['2FGAttempts'] = boxscore_df['2FGMade'] + boxscore_df['2FGMissed']
    boxscore_df['2FG%'] = round(boxscore_df.apply(lambda x: (x['2FGMade'] / x['2FGAttempts'] * 100) if x['2FGAttempts'] != 0 else 0, axis=1),2)

    boxscore_df['3FGAttempts'] = boxscore_df['3FGMade'] + boxscore_df['3FGMissed']
    boxscore_df['3FG%'] = round(boxscore_df.apply(lambda x: (x['3FGMade'] / x['3FGAttempts'] * 100) if x['3FGAttempts'] != 0 else 0, axis=1),2)

    boxscore_df['TRB'] = boxscore_df['DReb'] + boxscore_df['OReb']
    boxscore_df['Points'] = (boxscore_df['2FGMade'] * 2 + boxscore_df['3FGMade'] * 3 + boxscore_df['FTMade'])
    # boxscore_df['PPG'] = (boxscore_df['2FGMade'] * 2 + boxscore_df['3FGMade'] * 3 + boxscore_df['FTMade']) / boxscore_df.rsc.nunique()
    boxscore_df['PER'] = ((boxscore_df['2FGMade'] + boxscore_df['3FGMade']) - (boxscore_df['2FGMissed'] + boxscore_df['3FGMissed']) + boxscore_df['FTMade'] - boxscore_df['FTMissed']
                + boxscore_df['DReb'] + boxscore_df['Assist'] + boxscore_df['Steal'] + boxscore_df['Block'] - boxscore_df['CommittedFouls'] - boxscore_df['Turnover'] + boxscore_df['DrawnFouls'])
    return boxscore_df

def create_boxscore_one_game(game1):
    
    
    # Filter relevant columns for analysis
    player_stats_df = game1[['rsc','name', 'Action']]

    # Group by player and perform aggregation
    player_stats = player_stats_df.groupby(['rsc','name', 'Action']).size().reset_index(name='count')

    boxscore_df = get_stats_from_actions(player_stats)

    final_boxscore = add_columns(boxscore_df)

    return final_boxscore
