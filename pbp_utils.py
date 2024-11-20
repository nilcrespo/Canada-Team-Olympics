import pandas as pd
import urllib.request as urllib
from bs4 import BeautifulSoup


def get_all_games_tournament():
    """
    Returns a list of URLs for all games in a tournament.

    Returns:
        list: A list of URLs for all games in the tournament.
    """
    from selenium import webdriver 
    from selenium.webdriver.chrome.service import Service as ChromeService 
    from webdriver_manager.chrome import ChromeDriverManager 
    from selenium.webdriver.common.by import By
    
    url = 'https://www.fiba.basketball/basketballworldcup/2023/games'
    
    driver = webdriver.Chrome(service=ChromeService( 
        ChromeDriverManager().install())) 
    
    driver.get(url) 
    
    all_games_urls =[]
    elements = driver.find_elements(By.CSS_SELECTOR, '.games_list')
    for element in elements:
        a_tags = element.find_elements(By.TAG_NAME, 'a')
        for a_tag in a_tags:
            href = a_tag.get_attribute('href')
            if 'video' not in href:
                print(href)
                all_games_urls.append(href)
    driver.quit()
    return all_games_urls


def get_country_trigrams_dict():
    """
    Retrieve a dictionary of country trigrams from the FIBA Basketball World Cup 2023 website.

    Returns:
        dict: A dictionary where the keys are country names and the values are country codes.

    Example:
        >>> get_country_trigrams_dict()
        {'Argentina': 'ARG', 'Australia': 'AUS', 'Brazil': 'BRA', ...}
    """
    page_trigrams = urllib.urlopen("https://www.fiba.basketball/basketballworldcup/2023/groups#tab=round_FR")

    #######################################################################################
    #######################################################################################
    #######################################################################################
    #######################################################################################

    soup_trigrams = BeautifulSoup(page_trigrams, "html.parser")

    country_dict = {} 
    import re
    for div_tag in soup_trigrams.find_all("div", class_="qualifiers_group_table"):
        for a_tag in div_tag.find_all('a'): 
            href = a_tag.get('href') 
            if 'team' in href:
                country_code = a_tag.text.strip() 
                # country_code = re.search(r'iocCode=(\w+)', href).group(1) 
                country_name = href.split('/')[-1].replace('-', ' ') 
                country_dict[country_name] = country_code

    return country_dict


def get_starters_of_game(url):
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver = webdriver.Chrome()
    driver.get(url+'#|tab=boxscore')

    # Wait for the boxscore data to load
    wait = WebDriverWait(driver, 5)
    boxscore_data = wait.until(EC.presence_of_element_located((By.XPATH, '//div[@data-module-group="game-boxscore"]')))

    # Parse the boxscore data using BeautifulSoup
    soup = BeautifulSoup(boxscore_data.get_attribute('outerHTML'), 'html.parser')

    # Find the tables for each team
    tableA = soup.find('section', {'class': 'box-score_team-A'})
    tableB = soup.find('section', {'class': 'box-score_team-B'})
	
    boxscore_A = pd.read_html(str(tableA))[0]
    boxscore_A = boxscore_A[(boxscore_A['Min'] != 'Did not play  - Coach decision')]
    boxscore_A[['FG', 'FG%']] = boxscore_A['FG'].str.split(' ',expand=True)
    boxscore_A[['FT', 'FT%']] = boxscore_A['FT'].str.split(' ',expand=True)
    boxscore_A[['2Pts', '2Pts%']] = boxscore_A['2Pts'].str.split(' ',expand=True)
    boxscore_A[['3Pts', '3Pts%']] = boxscore_A['3Pts'].str.split(' ',expand=True)

    boxscore_B = pd.read_html(str(tableB))[0]
    boxscore_B = boxscore_B[(boxscore_B['Min'] != 'Did not play  - Coach decision')]
    boxscore_B[['FG', 'FG%']] = boxscore_B['FG'].str.split(' ',expand=True)
    boxscore_B[['FT', 'FG%']] = boxscore_B['FT'].str.split(' ',expand=True)
    boxscore_B[['2Pts', '2Pts%']] = boxscore_B['2Pts'].str.split(' ',expand=True)
    boxscore_B[['3Pts', '3Pts%']] = boxscore_B['3Pts'].str.split(' ',expand=True)

    # Find the rows in the tables
    rowsA = tableA.find_all('tr', {'class': 'x--player-is-starter'})
    rowsB = tableB.find_all('tr', {'class': 'x--player-is-starter'})

    # Extract the names of the starting players for each team
    starters_A = [row.find('td', {'class': 'name'}).text.strip() for row in rowsA]
    starters_B = [row.find('td', {'class': 'name'}).text.strip() for row in rowsB]

    driver.quit()
    return starters_A, starters_B, boxscore_A, boxscore_B



def get_team_actions(side,trigram,num_quarters, quarter, soup):
    """
    This function retrieves the actions performed by a specific team during a given quarter of a game.

    Parameters:
    - side (str): The side of the team ('A' or 'B').
    - quarter (int): The quarter number (1, 2, 3, or 4).
    - soup (BeautifulSoup object): The BeautifulSoup object containing the HTML data.

    Returns:
    - df (DataFrame): A pandas DataFrame containing the extracted information for each action performed by the team during the specified quarter.

    """
    import pandas as pd
    actions = soup.find_all("ul", class_="actions-list period_select_dependable")[num_quarters-quarter].find_all("li", class_=f"action-item x--team-{side}")
    df = pd.DataFrame()
    for i,action in enumerate(actions):


        #Extract relevant information
        team_flag_src = action.find('img', class_='nat-flag')['src']
        score_A = int(action.find('span', class_='score-A').text)
        score_B = int(action.find('span', class_='score-B').text)
        period = action.find('span', class_='period').text
        time = action.find('span', class_='time').text
		
        try:
            athlete_bib = int(action.find('span', class_='bib').text)
            athlete_name = action.find('span', class_='athlete-name').text
        except:
            athlete_bib = None
            athlete_name = ""
        action_description = action.find('span', class_='action-description').text

        # Create a DataFrame
        data = {
            'Team': trigram,
            'Team_Flag_Src': [team_flag_src],
            'Score_A': [score_A],
            'Score_B': [score_B],
            'Period': [period],
            'Time': [time],
            'Number': [athlete_bib],
            'Player': [athlete_name],
            'Action_Description': [action_description]
        }

        action_df = pd.DataFrame(data)

        # Display the DataFrame
        df = pd.concat([df, action_df])
		
    data = {
            'Team': None,
            'Team_Flag_Src': None,
            'Score_A': [score_A],
            'Score_B': [score_B],
            'Period': [period],
            'Time': ['00:00'],
            'Number': '',
            'Player': '',
            'Action_Description': ['End of quarter']
        }

    action_df = pd.DataFrame(data)

    # Display the DataFrame
    df = pd.concat([df, action_df])
    df['Total_Seconds'] = pd.to_timedelta('00:' + df['Time']).dt.total_seconds() + (((4 - min(quarter, 4)) * 600) + min(1, (num_quarters-quarter)) * 300)
    return df


def custom_sort_pbp(df):
    instants_with_subst  = list(df.groupby('Total_Seconds').apply(lambda x: x.Action_Description.str.contains('Subst'))[df.groupby('Total_Seconds').apply(lambda x: x.Action_Description.str.contains('Subst'))==True].reset_index().Total_Seconds.unique())

    df.loc[(df.Total_Seconds.isin(instants_with_subst)) & (df.Action_Description.str.contains('Subst')), 'sort_key'] = -1

    # For the rest of the rows, assign values based on the sorting criteria
    # Here, we assume sorting by the 'column_name' column
    df.loc[~((df.Total_Seconds.isin(instants_with_subst)) & (df.Action_Description.str.contains('Subst'))), 'sort_key'] = 0

    # Sort the DataFrame based on the sort key
    df_sorted = df.sort_values(by=['Total_Seconds','Score_A', 'Score_B','sort_key'], ascending=[False, True, True,False])

    # Optionally, drop the temporary column
    df_sorted.drop(columns=['sort_key'], inplace=True)
    return df_sorted

def concatenating_both_teams_quarter(num_quarters, quarter, soup, countryTri, oppTri):
    """
    Concatenates the actions performed by both teams during a specific quarter of a game.

    Parameters:
    - quarter (int): The quarter number (1, 2, 3, or 4).
    - soup (BeautifulSoup object): The BeautifulSoup object containing the HTML data.

    Returns:
    - df_q (DataFrame): A pandas DataFrame containing the concatenated information for each action performed by both teams during the specified quarter.

    """
    pbpQ_A =  get_team_actions('A',countryTri, num_quarters, quarter, soup)
    pbpQ_B =  get_team_actions('B',oppTri, num_quarters, quarter, soup)
    df_q = pd.concat([pbpQ_A, pbpQ_B]).sort_values(by='Total_Seconds')
    return df_q




def pbpParser(actions, players, times, team, quarter, Lineup, countryTri, OpponentLineup, outputWriter):

	for action in actions:
		action = (action.get_text())

	for player in players:
		player = (player.get_text()).strip()
		player = player.split('#', 1)[-1]

	for time in times:
		time = (time.get_text())

	for team in team:
		team = team.get('title')

	if (action == "Substitution in"
		and team == countryTri):
			Lineup.append(player)

	if (action == "Substitution out"
	and team == countryTri):
		Lineup.remove(player)

	if (action == "Substitution in"
	and team != countryTri):
		OpponentLineup.append(player)

	if (action == "Substitution out"
	and team != countryTri):
		OpponentLineup.remove(player)

	if (action in ("2pt jump shot made", "tip in made", "layup made", "dunk made")
	and team == countryTri):
		points = 2
		OPPpoints = -2

	elif (action in ("3pt shot made")
	and team == countryTri):
		points = 3
		OPPpoints = -3

	elif (action in ("2pt jump shot made", "tip in made", "layup made", "dunk made")
	and team != countryTri):
		points = -2
		OPPpoints = 2

	elif (action in ("3pt shot made")
	and team != countryTri):
		points = -3
		OPPpoints = 3

	elif (action in ("1st free throw made","1st of 2 free throws made","1st of 3 free throws made", "2nd of 2 free throws made","2nd of 3 free throws made", "3rd of 3 free throws made")
	and team != countryTri):
		points = -1
		OPPpoints = 1

	elif (action in ("1st free throw made","1st of 2 free throws made","1st of 3 free throw made", "2nd of 2 free throws made","2nd of 3 free throws made", "3rd of 3 free throws made")
	and team == countryTri):
		points = 1
		OPPpoints = -1				
	else:
		points = 0
		OPPpoints = 0

	if (action in ("2pt jump shot missed", "3pt shot missed", "2pt jump shot made", "3pt shot missed",\
		"tip in made", "layup made", "dunk made", "3pt shot made", "tip in missed", "layup missed", "dunk missed")
	and team == countryTri):
		FGA = 1
	else:
		FGA = 0

	if (action in ("2pt jump shot missed", "3pt shot missed", "2pt jump shot made", "3pt shot missed",\
		"tip in made", "layup made", "dunk made", "3pt shot made", "tip in missed", "layup missed", "dunk missed")
	and team != countryTri):
		OPPFGA = 1
	else:
		OPPFGA = 0

	if (action in ("1st free throw made","1st free throw missed","1st of 2 free throws made", "1st of 3 free throws made", "2nd of 2 free throws made",\
		"2nd of 3 free throws made", "3rd of 3 free throws made", "1st of 2 free throws missed",\
		"1st of 3 free throws missed", "2nd of 2 free throws missed","2nd of 3 free throws missed", "3rd of 3 free throws missed")
	and team == countryTri):
		FTA = 1
	else:
		FTA = 0

	if (action in ("1st free throw made","1st free throw missed","1st of 2 free throws made", "1st of 3 free throws made", "2nd of 2 free throws made",\
		"2nd of 3 free throws made", "3rd of 3 free throws made", "1st of 2 free throws missed",\
		"1st of 3 free throws missed", "2nd of 2 free throws missed","2nd of 3 free throws missed", "3rd of 3 free throws missed")
	and team != countryTri):
		OPPFTA = 1
	else:
		OPPFTA = 0

	if action in ("offensive rebound", "team offensive rebound") and team == countryTri:
		oREB = 1
	else:
		oREB = 0

	if action in ("offensive rebound", "team offensive rebound") and team != countryTri:
		OPPoREB = 1
	else:
		OPPoREB = 0

	if action in ("defensive rebound", "team defensive rebound") and team == countryTri:
		dREB = 1
	else:
		dREB = 0

	if action in ("defensive rebound", "team defensive rebound") and team != countryTri:
		OPPdREB = 1
	else:
		OPPdREB = 0

	if action.startswith("turnover") and team == countryTri:
		TOV = 1
	else:
		TOV = 0

	if action.startswith("turnover") and team != countryTri:
		OPPTOV = 1
	else:
		OPPTOV = 0

	Lineup.sort()
	LineupFormatted = ' | '.join(Lineup)
	OpponentLineup.sort()
	OppLineupFormatted = ' | '.join(OpponentLineup)

	#if(len(Lineup) == 5 and len(OpponentLineup) == 5):
	outputWriter.writerow([quarter, time, player, team, action, LineupFormatted, OppLineupFormatted, points, OPPpoints, FGA, OPPFGA, FTA, OPPFTA, oREB, OPPoREB, dREB, OPPdREB, TOV, OPPTOV])
