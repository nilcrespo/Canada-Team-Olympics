import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib.request as urllib
import time

from cpsat_utils import time_to_seconds, get_quarter_from_period

def fix_boxscore_df(boxscore_df):
    # Remove the "Did not play - Coach decision" rows
    boxscore_df = boxscore_df[(boxscore_df['MIN'] != 'Did not play  - Coach decision')&(boxscore_df['MIN'] != 'Did Not Play')]

    # Split the FG column into FG and FG%
    boxscore_df[['FG', 'FG%']] = boxscore_df['FG'].str.split('(',expand=True)
    boxscore_df['FG%'] = boxscore_df['FG%'].str.replace(')', '')

    # Split the FT column into FT and FT%
    boxscore_df[['FT', 'FT%']] = boxscore_df['FT'].str.split('(',expand=True)
    boxscore_df['FT%'] = boxscore_df['FT%'].str.replace(')', '')

    # Split the 2PT FG column into 2PT FG and 2PT FG%
    boxscore_df[['2PT FG', '2PT FG%']] = boxscore_df['2PT FG'].str.split('(',expand=True)
    boxscore_df['2PT FG%'] = boxscore_df['2PT FG%'].str.replace(')', '')

    # Split the 3PT FG column into 3PT FG and 3PT FG%
    boxscore_df[['3PT FG', '3PT FG%']] = boxscore_df['3PT FG'].str.split('(',expand=True)
    boxscore_df['3PT FG%'] = boxscore_df['3PT FG%'].str.replace(')', '')

    return boxscore_df


def get_starters_of_game(url):
    b_team = url.split('-')[-1]
    driver = webdriver.Chrome()
    driver.get(url+'#boxscore')

    # Wait for the boxscore data to load
    wait = WebDriverWait(driver, 5)
    boxscore_data = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="radix-:rb:-content-boxscore"]/div[2]/div/div[1]')))


    # Handle the cookie consent button
    try:
        cookie_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
        cookie_button.click()
    except:
        try:
            cookie_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-banner-sdk')))
            cookie_button.click()
        except Exception as e:
            print("Cookie consent button not found or already accepted.")


    # Parse the boxscore data using BeautifulSoup
    soup = BeautifulSoup(boxscore_data.get_attribute('innerHTML'), 'html.parser')

    # Find the tables for each team
    tableA = soup.find('table')

    boxscore_A = pd.read_html(str(tableA))[0]
    boxscore_A = fix_boxscore_df(boxscore_A)
    starters_A = boxscore_A[boxscore_A['Players'].str.contains(r'\*')]['Players'].str.replace(' *', '').tolist()


    # Click on the "Greece" tab
    greece_tab = driver.find_element(By.XPATH, f'//div[@id="team-selection-{b_team}"]')
    greece_tab.click()

    # Wait for the Greece boxscore data to load
    bteam_boxscore_data = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="radix-:rb:-content-boxscore"]/div[2]/div/div[1]')))

    # Parse the Greece boxscore data using BeautifulSoup
    soup = BeautifulSoup(bteam_boxscore_data.get_attribute('innerHTML'), 'html.parser')

    # Find the tables for Greece team
    tableB = soup.find('table')

    boxscore_B = pd.read_html(str(tableB))[0]
    boxscore_B = fix_boxscore_df(boxscore_B)
    starters_B = boxscore_B[boxscore_B['Players'].str.contains(r'\*')]['Players'].str.replace(' *', '').tolist()

    driver.quit()
    return starters_A, starters_B, boxscore_A, boxscore_B


def fixing_time_boxscore(boxscore_df):
    # Create a mask for rows that do not contain 'Totals' or 'Team/Coaches' in the '#' column
    mask = ~boxscore_df['#'].str.contains('Totals|Team/Coaches|TOTAL')

    # Use .loc with the mask to operate directly on the original DataFrame
    boxscore_df.loc[mask, 'time_seconds'] = boxscore_df.loc[mask, 'MIN'].apply(time_to_seconds)
    return boxscore_df[mask]


def get_game_stats(url, num_quarters=4):
    # Initialize the WebDriver
    driver = webdriver.Chrome()
    driver.get(url + '#playByPlay')

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Attempt to close the cookie consent banner if it exists
    try:
        cookie_consent_button = wait.until(EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler')))
        cookie_consent_button.click()
        print("Cookie consent banner closed.")
    except Exception as e:
        print("No cookie consent banner found or unable to close it:", e)

    # Define the quarter tabs and div classes
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']
    div_classes = ['ljnvyk5 ljnvyk3', 'ljnvyk5 ljnvyk1 ljnvyk4', 'ljnvyk5 ljnvyk1']

    # Check for OT tabs and add them to the quarters list
    for i in range(1, 6):  # Assuming a maximum of 5 OT periods
        try:
            ot_tab = driver.find_element(By.ID, f'game-tab-roster-teams-quarter-OT{i}')
            quarters.append(f'OT{i}')
        except Exception as e:
            break  # Stop checking if an OT tab is not found

    # Initialize an empty DataFrame
    df = pd.DataFrame()

    for quarter in quarters:

        # Click on the quarter tab
        quarter_tab = wait.until(EC.element_to_be_clickable((By.ID, f'game-tab-roster-teams-quarter-{quarter}')))
        quarter_tab.click()
        print(f"Clicked on quarter tab: {quarter}")
        
        # Parse the page source with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find all actions for the current quarter
        actions = []
        for div_class in div_classes:
            actions.extend(soup.find_all("div", class_=div_class))
        
        for action in actions:
            time_ =  action.find('div', class_="ljnvyk7").get_text(separator='/', strip=True)
            flag = action.find_all( 'img', {'class':'o3vl2x8'})[0]['src']
            period = quarter
            all_main_text = action.find('div', class_="ljnvykd").get_text(separator='/', strip=True)
            score = action.find('div', class_="ljnvykf").get_text(separator=' ', strip=True)
            score_A = score.split(' - ')[0]
            score_B = score.split(' - ')[1]
            if len(all_main_text.split('/'))>3:
                player = all_main_text.split('/')[0]
                action_description = all_main_text.split('/')[2]
            elif len(all_main_text.split('/'))==3:
                player = all_main_text.split('/')[0]
                action_description = all_main_text.split('/')[1]
            elif len(all_main_text.split('/'))==2:
                player = ''
                action_description = all_main_text.split('/')[0]

            # Create a DataFrame
            data = {
                'Team_Flag_Src': [flag],
                'Score_A': [score_A],
                'Score_B': [score_B],
                'Period': [period],
                'Time': [time_],
                'Player': [player],
                'Action_Description': [action_description]
            }

            action_df = pd.DataFrame(data)

            # Display the DataFrame
            df = pd.concat([df, action_df])
        data = {
            'Team_Flag_Src': None,
            'Score_A': [score_A],
            'Score_B': [score_B],
            'Period': [period],
            'Time': ['00:00'],
            'Player': '',
            'Action_Description': ['End of quarter']
        }

        action_df = pd.DataFrame(data)

        # Display the DataFrame
        df = pd.concat([df, action_df])

    def calculate_total_seconds(row, num_quarters=4):
        minutes, seconds = map(int, row['Time'].split(':'))
        total_seconds = minutes * 60 + seconds
        quarter = get_quarter_from_period(row['Period'])
        
        # Calculate cumulative seconds
        if num_quarters <= 4:
            cumulative_seconds = (num_quarters - quarter) * 600  # 600 seconds per regular quarter
        else:
            cumulative_seconds = (((4 - min(quarter, 4)) * 600) + min(1, (num_quarters-quarter)) * 300)  # 300 seconds per OT period
        
        return total_seconds + cumulative_seconds

    # Apply the function to the DataFrame
    df['Total_Seconds'] = df.apply(lambda row: calculate_total_seconds(row, num_quarters), axis=1)

    # Close the WebDriver
    driver.quit()

    # Display the DataFrame
    return df



def get_final_pbp_dataset_big(url, save=True):
    from pbp_utils import get_country_trigrams_dict
    from cpsat_utils import get_quarter_from_period, remove_inconsistent_rows, swapping_subs_in_out, solve_optimization_problem
    starters_A, starters_B, boxscore_A, boxscore_B = get_starters_of_game(url)
    boxscore_A_players = fixing_time_boxscore(boxscore_A)
    boxscore_B_players = fixing_time_boxscore(boxscore_B)


    country_trigrams = get_country_trigrams_dict()

    soup = BeautifulSoup(urllib.urlopen(url), "html.parser")

    print("Locating Play By Play...")

    total_quarters_time = int(boxscore_A[boxscore_A['#']=='Totals']['MIN'].values[0])

    if total_quarters_time==200:
        total_quarters =  4
    else:
        ot_time = int((total_quarters_time - 200)/ 25)
        total_quarters = 4 + ot_time

    all_pbp = pd.DataFrame()
    home_team = url.split('/')[-1].split('-')[1]
    away_team = url.split('/')[-1].split('-')[2]

    all_pbp = get_game_stats(url)
    all_pbp.sort_values('Total_Seconds', inplace=True)


    player_numbers_A = dict(zip(boxscore_A[~boxscore_A['#'].str.contains('Team/Coaches|TOTAL')]['Players'].str.replace(' *', ''), boxscore_A[~boxscore_A['#'].str.contains('Team/Coaches|TOTAL')]['#']))
    player_numbers_B = dict(zip(boxscore_B[~boxscore_B['#'].str.contains('Team/Coaches|TOTAL')]['Players'].str.replace(' *', ''), boxscore_B[~boxscore_B['#'].str.contains('Team/Coaches|TOTAL')]['#']))
    
    # Function to map player to number and team
    def map_player_info(player):
        if player in player_numbers_A:
            return player_numbers_A[player], 'A'
        elif player in player_numbers_B:
            return player_numbers_B[player], 'B'
        else:
            return None, ''

    # Apply the function to create new columns
    all_pbp[['Number', 'Team']] = all_pbp['Player'].apply(lambda player: pd.Series(map_player_info(player)))


    all_pbp['quarter'] = all_pbp['Period'].apply(get_quarter_from_period)
    all_pbp.drop_duplicates(inplace=True)
    all_pbp = remove_inconsistent_rows(all_pbp)
    # all_pbp = all_pbp[~all_pbp.Number.isnull()].reset_index(drop=True)
    all_pbp = swapping_subs_in_out(all_pbp)
    all_pbp['time_elapsed'] = all_pbp['Total_Seconds'].shift(1)- all_pbp['Total_Seconds']

    truth_total_time_A =[int(time) for time in boxscore_A.loc[~boxscore_A['#'].str.contains('Team/Coaches|TOTAL'),'time_seconds'].tolist()]  # Assuming 'truth_total_time' is the column containing total time for each player
    team_names_A =boxscore_A.loc[~boxscore_A['#'].isin(['Totals','Team/Coaches']),'Players'].tolist() 
    truth_total_time_B = [int(time) for time in boxscore_B.loc[~boxscore_B['#'].str.contains('Team/Coaches|TOTAL'),'time_seconds'].tolist()]  # Assuming 'truth_total_time' is the column containing total time for each player
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
