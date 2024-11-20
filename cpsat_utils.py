from pbp_utils import get_starters_of_game, concatenating_both_teams_quarter, get_country_trigrams_dict
from bs4 import BeautifulSoup
import urllib.request as urllib
from ortools.sat.python import cp_model
import pandas as pd

def time_to_seconds(time_str):
    minutes, seconds = map(int, time_str.split(':'))
    return minutes * 60 + seconds


def fixing_time_boxscore(boxscore_df):
    # Create a mask for rows that do not contain 'Totals' or 'Team/Coaches' in the '#' column
    mask = ~boxscore_df['#'].str.contains('Totals|Team/Coaches')

    # Use .loc with the mask to operate directly on the original DataFrame
    boxscore_df.loc[mask, 'time_seconds'] = boxscore_df.loc[mask, 'Min'].apply(time_to_seconds)
    return boxscore_df[mask]




def custom_sort_pbp(df):
    instants_with_subst  = list(df.groupby('Total_Seconds').apply(lambda x: x.Action_Description.str.contains('Subst'))[df.groupby('Total_Seconds').apply(lambda x: x.Action_Description.str.contains('Subst'))==True].reset_index().Total_Seconds.unique())

    df.loc[(df.Total_Seconds.isin(instants_with_subst)) & (df.Action_Description.str.contains('Substitution out')), 'sort_key'] = -1
    df.loc[(df.Total_Seconds.isin(instants_with_subst)) & (df.Action_Description.str.contains('Substitution in')), 'sort_key'] = -2

    # For the rest of the rows, assign values based on the sorting criteria
    # Here, we assume sorting by the 'column_name' column
    df.loc[~((df.Total_Seconds.isin(instants_with_subst)) & (df.Action_Description.str.contains('Subst'))), 'sort_key'] = 0

    # Sort the DataFrame based on the sort key
    df_sorted = df.sort_values(by=['Total_Seconds','Score_A', 'Score_B','sort_key'], ascending=[False, True, True,False])

    # Optionally, drop the temporary column
    df_sorted.drop(columns=['sort_key'], inplace=True)
    return df_sorted



def remove_inconsistent_rows(df):
    # Get the indices of rows where the player action is "substitution in"
    substitution_in_indices = dict(zip(df[df['Action_Description'] == 'Substitution in'].index, df[df['Action_Description'] == 'Substitution in']['Player'].tolist()))

    last_rows = {}
    for index, player in substitution_in_indices.items():
        last_row = df.iloc[:index][df['Player'] == player].tail(1)
        if len(last_row) > 0:  
            if last_row['Action_Description'].values[0] != 'Substitution out' and last_row['quarter'].values[0] == df.loc[index]['quarter']:
                last_rows[index] = last_row

    # Delete rows of last_rows[last_rows.keys]
    for key in list(last_rows.keys()):
        df.drop(last_rows[key].index.values[0], inplace=True)
        
    return df


def swapping_subs_in_out(all_pbp):
    # Finding indices of rows with 'Substitution in' and 'Substitution out'
    indices_in = all_pbp.index[all_pbp['Action_Description'] == 'Substitution in']
    indices_out = all_pbp.index[all_pbp['Action_Description'] == 'Substitution out']
    indices = tuple(zip(indices_in, indices_out))
    # Reordering rows if 'Substitution out' comes after 'Substitution in'
    for index_in,index_out in indices:
        if index_out > index_in:
            # Swap the rows
            
            in_row = all_pbp.iloc[index_in].copy()
            out_row =all_pbp.iloc[index_out].copy()
            all_pbp.iloc[index_in] =  out_row
            all_pbp.iloc[index_out] = in_row
    all_pbp.reset_index(drop=True, inplace=True)
    return all_pbp


def solve_optimization_problem(N, T, truth_total_time, time_elapsed, team_names, player_action, descriptions, starters, quarters, team_action, team, total_quarters, flag_error=False):
    model = cp_model.CpModel()

    # Variables
    X_ij_A = [[model.NewIntVar(0, 1, f'X_{i}_{j}_A') for j in range(T)] for i in range(N)]

    # Constraints
    player_name_index_to_sub_out = []
    for j in range(T):
        if j==0:
            for i in range(N):
                if team_names[i] in starters:
                    model.Add(X_ij_A[i][j] == 1)

        model.Add(sum(X_ij_A[i][j] for i in range(N)) == 5)
        players_popped = 0
        for i in range(N):
            # Adding constraint only for actions corresponding to player i
            if 'ubstitution' not in descriptions[j] or team_action[j] != team:
                if quarters[j] == quarters[j-1]:
                    model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)
                if player_action[j] == team_names[i] and not flag_error:
                    model.Add(X_ij_A[i][j] == 1)

            elif 'ubstitution out' in descriptions[j] and team_action[j] == team:
                if player_action[j] == team_names[i]:
                    # If going out, the player was previously in the game
                    model.Add( X_ij_A[i][j-1] == 1)  
                    player_name_index_to_sub_out.append((i,j, team_names[i]))
                else:
                    model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)


            elif 'ubstitution in' in descriptions[j] and team_action[j] == team:
                if len(player_name_index_to_sub_out) > 0 and players_popped == 0:
                    player_index, time_index, player_name = player_name_index_to_sub_out[0]
                # Check if the player is involved in the substitution
                if player_action[j] == team_names[i]:
                    # If going in, the player should transition from 0 to 1
                    model.Add(X_ij_A[i][j] == 1)
                elif i ==  player_index and players_popped == 0:
                    model.Add(X_ij_A[player_index][j] == 0)
                    player_name_index_to_sub_out.pop(0)  # Remove the player from the list    
                    players_popped += 1           
                else:
                    model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)

                    
                

            # Total time constraint for player i 
    model.Add(sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T) for i in range(N)) == (4*3000 +(total_quarters-4)*1500))




    objective_expr = [model.NewIntVar(-100000, 100000, f'Objective_{i}') for i in range(N)]
    for i in range(N):
        model.AddAbsEquality(objective_expr[i], sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T)) - truth_total_time[i])

    # Objective
    
    # model.Minimize(sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T)) - X_ij_A_values.loc[j, f"X_{boxscore_A_players['#'].tolist()[i]}_j_A"] for i in range(N) for j in range(T)))
    model.Minimize(sum(objective_expr))


    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        # Retrieve solution
        solution_X_ij_A = [[solver.Value(X_ij_A[i][j]) for j in range(T)] for i in range(N)]
        return solution_X_ij_A
    else:
        return None
    


'''def solve_optimization_problem_old(N, T, truth_total_time, time_elapsed, team_names, player_action, descriptions, starters, quarters):
    model = cp_model.CpModel()

    # Variables
    X_ij_A = [[model.NewIntVar(0, 1, f'X_{i}_{j}_A') for j in range(T)] for i in range(N)]

    # Constraints
    
    for j in range(T):
        if j==0:
            for i in range(N):
                if team_names[i] in starters:
                    model.Add(X_ij_A[i][j] == 1)
        if 'ubstitution' not in descriptions[j]:
            model.Add(sum(X_ij_A[i][j] for i in range(N)) == 5)
        for i in range(N):
            # Adding constraint only for actions corresponding to player i
            if 'ubstitution' not in descriptions[j]:
                if quarters[j] == quarters[j-1]:
                    model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)
                if player_action[j] == team_names[i]:
                    model.Add(X_ij_A[i][j] == 1)
            elif 'ubstitution in' in descriptions[j]:
                # Check if the player is involved in the substitution
                if player_action[j] == team_names[i]:
                    # If going in, the player should transition from 0 to 1
                    model.Add(X_ij_A[i][j] == 1)
                elif player_action[j-1] == team_names[i] and 'ubstitution out' in descriptions[j-1]:
                    model.Add(X_ij_A[i][j] == 0)
                else:
                    model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)
            elif 'ubstitution out' in descriptions[j]:
                if player_action[j] == team_names[i]:
                    # If going out, the player should transition from 1 to 0
                    model.Add( X_ij_A[i][j+1] == 0)  
                elif player_action[j-1] == team_names[i] and 'ubstitution out' in descriptions[j-1]:
                    model.Add(X_ij_A[i][j] == 0)
                # else:
                    # model.Add(X_ij_A[i][j] - X_ij_A[i][j-1] == 0)
                    
                

            # Total time constraint for player i 
    model.Add(sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T) for i in range(N)) == 12000)




    objective_expr = [model.NewIntVar(-100000, 100000, f'Objective_{i}') for i in range(N)]
    for i in range(N):
        model.AddAbsEquality(objective_expr[i], sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T)) - truth_total_time[i])

    # Objective
    
    # model.Minimize(sum(X_ij_A[i][j] * int(time_elapsed[j]) for j in range(T)) - X_ij_A_values.loc[j, f"X_{boxscore_A_players['#'].tolist()[i]}_j_A"] for i in range(N) for j in range(T)))
    model.Minimize(sum(objective_expr))


    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print(solver.ResponseStats())

    if status == cp_model.OPTIMAL:
        # Retrieve solution
        solution_X_ij_A = [[solver.Value(X_ij_A[i][j]) for j in range(T)] for i in range(N)]
        return solution_X_ij_A
    else:
        return None'''


def parse_game_page(url):
    """
    Parses the game page and returns a BeautifulSoup object.
    """
    print("Parsing game page...")
    return BeautifulSoup(urllib.urlopen(url), "html.parser")

def calculate_total_quarters(boxscore_A):
    """
    Calculates the total number of quarters played in the game.
    """
    print("Calculating total quarters...")
    total_quarters_time = int(boxscore_A[boxscore_A['#']=='Totals']['Min'].values[0])
    if total_quarters_time == 200:
        return 4
    else:
        ot_time = int((total_quarters_time - 200) / 25)
        return 4 + ot_time

def get_teams_from_url(url, country_trigrams):
    home_team = country_trigrams[url.split('/')[-1].split('-')[0]]
    away_team = country_trigrams[url.split('/')[-1].split('-')[1]]
    return home_team, away_team

def get_quarter_from_period(period):
    if 'OT' in period:
        return 4 + int(period[2])
    else:
        return int(period[1])

def compile_play_by_play_data(total_quarters, soup, country_trigrams, url):
    """
    Compiles all play-by-play data for the game.
    """
    print("Compiling Play By Play data...")
    all_pbp = pd.DataFrame()
    home_team, away_team = get_teams_from_url(url, country_trigrams)
    for i in range(1, total_quarters + 1):
        pbpQ_ = concatenating_both_teams_quarter(total_quarters, i, soup, home_team, away_team)
        pbpQ = custom_sort_pbp(pbpQ_)
        all_pbp = pd.concat([all_pbp, pbpQ])
    all_pbp['quarter'] = get_quarter_from_period(all_pbp['Period'])
    all_pbp.drop_duplicates(inplace=True)
    all_pbp = remove_inconsistent_rows(all_pbp)
    all_pbp = all_pbp[~all_pbp.Number.isnull()].reset_index(drop=True)
    all_pbp = swapping_subs_in_out(all_pbp)
    all_pbp['time_elapsed'] = all_pbp['Total_Seconds'].shift(1) - all_pbp['Total_Seconds']
    return all_pbp

def process_pbp_data(all_pbp, starters_A, starters_B, boxscore_A, boxscore_B, boxscore_A_players, boxscore_B_players, total_quarters):
    """
    Processes the play-by-play data, including optimization and validation.
    """
    print("Processing Play By Play data...")
    # Extract relevant data
    time_elapsed, players_actions, descriptions, quarters, team_action = extract_pbp_data(all_pbp)
    
    # Solve optimization problem for Team A
    solve_and_validate_optimization(all_pbp, boxscore_A, boxscore_A_players, time_elapsed, players_actions, descriptions, starters_A, quarters, team_action, 'A', total_quarters)
    
    # Solve optimization problem for Team B
    solve_and_validate_optimization(all_pbp, boxscore_B, boxscore_B_players, time_elapsed, players_actions, descriptions, starters_B, quarters, team_action, 'B', total_quarters)

def extract_pbp_data(all_pbp):
    """
    Extracts relevant data from the play-by-play DataFrame.
    """
    time_elapsed = all_pbp['time_elapsed'].fillna(0).tolist()
    players_actions = all_pbp['Player'].str.replace('  ', ' ').tolist()
    descriptions = all_pbp['Action_Description'].tolist()
    quarters = all_pbp['Period'].tolist()
    team_action = all_pbp['Team'].tolist()
    return time_elapsed, players_actions, descriptions, quarters, team_action

def solve_and_validate_optimization(all_pbp, boxscore, boxscore_players, time_elapsed, players_actions, descriptions, starters, quarters, team_action, team_label, total_quarters):
    """
    Solves the optimization problem for a team and validates the results.
    """
    print(f"Solving optimization problem for Team {team_label}...")
    N = len(boxscore_players)
    T = len(all_pbp)
    truth_total_time = [int(time) for time in boxscore.loc[~boxscore['#'].isin(['Totals','Team/Coaches']), 'time_seconds'].tolist()]
    team_names = boxscore.loc[~boxscore['#'].isin(['Totals','Team/Coaches']), 'Players'].tolist()
    
    solution = solve_optimization_problem(N, T, truth_total_time, time_elapsed, team_names, players_actions, descriptions, starters, quarters, team_action, team_label, total_quarters)
    if solution is not None:
        for i, row in enumerate(solution):
            all_pbp.loc[:, f"X_{boxscore_players['#'].tolist()[i]}_j_{team_label}"] = row
    else:
        print("No solution found. Trying again!")
    validate_solution(all_pbp, boxscore, solution, time_elapsed, team_label)

def validate_solution(all_pbp, boxscore, T, time_elapsed, team_label):
    """
    Validates the solution of the optimization problem.
    """
    print(f"Validating solution for Team {team_label}...")
    
    i =0
    sum_pred = 0
    sum_actual = 0
    for col in all_pbp.columns:
        if f'j_{team_label}' in col:
            print(f'For player number {col.split("_")[1]}: ----- We predict {sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))} vs {boxscore.time_seconds.iloc[i]} real seconds')
            assert sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T)) == boxscore.time_seconds.iloc[i]
            sum_pred += sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))
            sum_actual += boxscore.time_seconds.iloc[i]
            i += 1
    assert sum_pred == sum_actual

def get_final_pbp_dataset(url):
    """
    Main function to get the final play-by-play dataset.
    """
    # Extract initial data
    starters_A, starters_B, boxscore_A, boxscore_B = get_starters_of_game(url)
    boxscore_A_players = fixing_time_boxscore(boxscore_A)
    boxscore_B_players = fixing_time_boxscore(boxscore_B)

    # Get country trigrams
    country_trigrams = get_country_trigrams_dict()

    # Parse the game page
    soup = parse_game_page(url)

    # Determine total quarters
    total_quarters = calculate_total_quarters(boxscore_A)

    # Compile all play-by-play data
    all_pbp = compile_play_by_play_data(total_quarters, soup, country_trigrams, url)

    # Process play-by-play data
    process_pbp_data(all_pbp, starters_A, starters_B, boxscore_A, boxscore_B, boxscore_A_players, boxscore_B_players, total_quarters)

    return all_pbp















def get_final_pbp_dataset_big(url, save=True, preolympic=False):
    starters_A, starters_B, boxscore_A, boxscore_B = get_starters_of_game(url)
    boxscore_A_players = fixing_time_boxscore(boxscore_A)
    boxscore_B_players = fixing_time_boxscore(boxscore_B)


    country_trigrams = get_country_trigrams_dict()

    soup = BeautifulSoup(urllib.urlopen(url), "html.parser")

    print("Locating Play By Play...")

    total_quarters_time = int(boxscore_A[boxscore_A['#']=='Totals']['Min'].values[0])

    if total_quarters_time==200:
        total_quarters =  4
    else:
        ot_time = int((total_quarters_time - 200)/ 25)
        total_quarters = 4 + ot_time

    all_pbp = pd.DataFrame()

    home_team = country_trigrams[url.split('/')[-1].split('-')[0]]
    away_team = country_trigrams[url.split('/')[-1].split('-')[1]]
    for i in range(1, total_quarters+1):
        pbpQ_ = concatenating_both_teams_quarter(total_quarters, i, soup, home_team, away_team)
        pbpQ= custom_sort_pbp(pbpQ_)
        all_pbp = pd.concat([all_pbp, pbpQ])

    all_pbp['quarter'] = all_pbp['Period'].apply(get_quarter_from_period)
    all_pbp.drop_duplicates(inplace=True)
    all_pbp = remove_inconsistent_rows(all_pbp)
    all_pbp = all_pbp[~all_pbp.Number.isnull()].reset_index(drop=True)
    all_pbp = swapping_subs_in_out(all_pbp)
    all_pbp['time_elapsed'] = all_pbp['Total_Seconds'].shift(1)- all_pbp['Total_Seconds']

    truth_total_time_A =[int(time) for time in boxscore_A.loc[~boxscore_A['#'].isin(['Totals','Team/Coaches']),'time_seconds'].tolist()]  # Assuming 'truth_total_time' is the column containing total time for each player
    team_names_A =boxscore_A.loc[~boxscore_A['#'].isin(['Totals','Team/Coaches']),'Players'].tolist() 
    truth_total_time_B = [int(time) for time in boxscore_B.loc[~boxscore_B['#'].isin(['Totals','Team/Coaches']),'time_seconds'].tolist()]  # Assuming 'truth_total_time' is the column containing total time for each player
    team_names_B = boxscore_B.loc[~boxscore_B['#'].isin(['Totals','Team/Coaches']),'Players'].tolist()

    time_elapsed = all_pbp['time_elapsed'].fillna(0).tolist()
    players_actions = all_pbp['Player'].str.replace('  ', ' ').tolist()
    descriptions = all_pbp['Action_Description'].tolist()
    quarters = all_pbp['Period'].tolist()
    team_action = all_pbp['Team'].tolist()


    N_A = len(team_names_A)
    N_B = len(team_names_B)
    T = len(all_pbp)

    solution_X_ij_A = solve_optimization_problem(N_A, T, truth_total_time_A, time_elapsed, team_names_A, players_actions, descriptions, starters_A, quarters, team_action, home_team, total_quarters)
    if solution_X_ij_A is None:
        solution_X_ij_A = solve_optimization_problem(N_A, T, truth_total_time_A, time_elapsed, team_names_A, players_actions, descriptions, starters_A, quarters, team_action, home_team, total_quarters, flag_error=True)

    if solution_X_ij_A is not None:
        for i,row in enumerate(solution_X_ij_A):
            all_pbp.loc[:, f"X_{boxscore_A_players['#'].tolist()[i]}_j_A"] = row
    else:
        print("No solution found.")

    i =0
    sum_pred = 0
    sum_actual = 0
    for col in all_pbp.columns:
        if 'j_A' in col:
            print(f'For player number {col.split("_")[1]}: ----- We predict {sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))} vs {boxscore_A.time_seconds.iloc[i]} real seconds')
            assert sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T)) == boxscore_A.time_seconds.iloc[i]
            sum_pred += sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))
            sum_actual += boxscore_A.time_seconds.iloc[i]
            i += 1
    assert sum_pred == sum_actual

    solution_X_ij_B = solve_optimization_problem(N_B, T, truth_total_time_B, time_elapsed, team_names_B, players_actions, descriptions, starters_B, quarters, team_action, away_team, total_quarters)
    if solution_X_ij_B is None:
        solution_X_ij_B = solve_optimization_problem(N_B, T, truth_total_time_B, time_elapsed, team_names_B, players_actions, descriptions, starters_B, quarters, team_action, away_team, total_quarters, flag_error=True)
    if solution_X_ij_B is not None:
        for i,row in enumerate(solution_X_ij_B):
            all_pbp.loc[:, f"X_{boxscore_B_players['#'].tolist()[i]}_j_B"] = row
    else:
        print("No solution found.")

    i =0
    sum_pred = 0
    sum_actual = 0
    for col in all_pbp.columns:
        if 'j_B' in col:
            print(f'For player number {col.split("_")[1]}: ----- We predict {sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))} vs {boxscore_B.time_seconds.iloc[i]} real seconds')
            assert sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T)) == boxscore_B.time_seconds.iloc[i]
            sum_pred += sum(all_pbp[col][j] * int(time_elapsed[j]) for j in range(T))
            sum_actual += boxscore_B.time_seconds.iloc[i]
            i += 1
    assert sum_pred == sum_actual

    if save:
        all_pbp.to_csv(f"{url.split('/')[-1]}.csv", index=False)
    return all_pbp
