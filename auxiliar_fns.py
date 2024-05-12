from flask import Flask, render_template, abort
import requests
import json
from collections import defaultdict
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
pd.options.display.float_format = "{:,.2f}".format

app = Flask(__name__)


# Sample data
rosters = {
    "Europe": {
        "France": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=FRA',
            "players": [
                # Add more players
            ]
        },
        "Germany": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=GER',
            "players": [
                # Add players
            ]
        },
        "Serbia": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=SRB',
            "players": [
                # Add players
            ]
        },
        # Add more European countries and their rosters
    },
    "Americas": {
        "Canada": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=CAN',
            "players": [
                # Add more players
            ]
        },
        "United States": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=USA',
            "players": [
                # Add players
            ]
        },
        # Add more American countries and their rosters
    },
    "Asia": {
        "Japan": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=JPN',
            "players": [
                # Add more players
            ]
        },
        # Add more Asian countries and their rosters
    },
    "Oceania": {
        "Australia": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=AUS',
            "players": [
                # Add players
            ]
        },
        # Add more Australian countries and their rosters
    },
    "Africa": {
        "South Sudan": {
            "flag": 'https://www.fiba.basketball/api/img/team/logoflag/0?sizeType=Big&backgroundType=Light&patternType=default_big&eventId=208722&iocCode=SSD',
            "players": [
                # Add more players
            ]
        },
        # Add more African countries and their rosters
    },
}
def get_continent(country):
    continents = {
        'Africa': ['Algeria', 'Angola', 'Benin', 'Botswana', 'Burkina Faso', 'Burundi', 'Cameroon', 'Cape Verde', 'Central African Republic', 'Chad', 'Comoros', 'Democratic Republic of the Congo', 'Djibouti', 'Egypt', 'Equatorial Guinea', 'Eritrea', 'Eswatini', 'Ethiopia', 'Gabon', 'Gambia', 'Ghana', 'Guinea', 'Guinea-Bissau', 'Ivory Coast', 'Kenya', 'Lesotho', 'Liberia', 'Libya', 'Madagascar', 'Malawi', 'Mali', 'Mauritania', 'Mauritius', 'Morocco', 'Mozambique', 'Namibia', 'Niger', 'Nigeria', 'Republic of the Congo', 'Rwanda', 'Sao Tome and Principe', 'Senegal', 'Seychelles', 'Sierra Leone', 'Somalia', 'South Africa', 'South Sudan', 'Sudan', 'Tanzania', 'Togo', 'Tunisia', 'Uganda', 'Zambia', 'Zimbabwe'],
        'Asia': ['Afghanistan', 'Armenia', 'Azerbaijan', 'Bahrain', 'Bangladesh', 'Bhutan', 'Brunei', 'Cambodia', 'China', 'Cyprus', 'Georgia', 'India', 'Indonesia', 'Iran', 'Iraq', 'Israel', 'Japan', 'Jordan', 'Kazakhstan', 'Kuwait', 'Kyrgyzstan', 'Laos', 'Lebanon', 'Malaysia', 'Maldives', 'Mongolia', 'Myanmar', 'Nepal', 'North Korea', 'Oman', 'Pakistan', 'Palestine', 'Philippines', 'Qatar', 'Russia', 'Saudi Arabia', 'Singapore', 'South Korea', 'Sri Lanka', 'Syria', 'Taiwan', 'Tajikistan', 'Thailand', 'Timor-Leste', 'Turkey', 'Turkmenistan', 'United Arab Emirates', 'Uzbekistan', 'Vietnam', 'Yemen'],
        'Europe': ['Albania', 'Andorra', 'Austria', 'Belarus', 'Belgium', 'Bosnia and Herzegovina', 'Bulgaria', 'Croatia', 'Czech Republic', 'Denmark', 'Estonia', 'Finland', 'France', 'Germany', 'Greece', 'Hungary', 'Iceland', 'Ireland', 'Italy', 'Kosovo', 'Latvia', 'Liechtenstein', 'Lithuania', 'Luxembourg', 'Malta', 'Moldova', 'Monaco', 'Montenegro', 'Netherlands', 'North Macedonia', 'Norway', 'Poland', 'Portugal', 'Romania', 'San Marino', 'Serbia', 'Slovakia', 'Slovenia', 'Spain', 'Sweden', 'Switzerland', 'Ukraine', 'United Kingdom', 'Vatican City'],
        'Americas': ['Antigua and Barbuda', 'Bahamas', 'Barbados', 'Belize', 'Canada', 'Costa Rica', 'Cuba', 'Dominica', 'Dominican Republic', 'El Salvador', 'Grenada', 'Guatemala', 'Haiti', 'Honduras', 'Jamaica', 'Mexico', 'Nicaragua', 'Panama', 'Saint Kitts and Nevis', 'Saint Lucia', 'Saint Vincent and the Grenadines', 'Trinidad and Tobago', 'United States', 'Argentina', 'Bolivia', 'Brazil', 'Chile', 'Colombia', 'Ecuador', 'Guyana', 'Paraguay', 'Peru', 'Suriname', 'Uruguay', 'Venezuela'],
        'Oceania': ['Australia', 'Fiji', 'Kiribati', 'Marshall Islands', 'Micronesia', 'Nauru', 'New Zealand', 'Palau', 'Papua New Guinea', 'Samoa', 'Solomon Islands', 'Tonga', 'Tuvalu', 'Vanuatu'],
    }
    
    for continent, countries in continents.items():
        if country in countries:
            return continent
    print(f'Country {country} not in continents dict')
    
NBA_teams_dict = {'BOS': 'Boston Celtics, USA', 
                  'MIL': 'Milwaukee Bucks, USA', 
                  'CLE': 'Cleveland Cavaliers, USA', 
                  'ORL': 'Orlando Magic, USA', 
                  'NYK': 'New York Knicks, USA', 
                  'IND': 'Indiana Pacers, USA', 
                  'MIA': 'Miami Heat, USA', 
                  'PHI': 'Philadelphia 76ers, USA', 
                  'CHI': 'Chicago Bulls, USA', 
                  'ATL': 'Atlanta Hawks, USA', 
                  'BRK': 'Brooklyn Nets, USA', 
                  'TOR': 'Toronto Raptors, Canada', 
                  'CHO': 'Charlotte Hornets, USA', 
                  'WAS': 'Washington Wizards, USA', 
                  'DET': 'Detroit Pistons, USA', 
                  'MIN': 'Minnesota Timberwolves, USA', 
                  'DEN': 'Denver Nuggets, USA', 
                  'OKC': 'Oklahoma City Thunder, USA', 
                  'LAC': 'Los Angeles Clippers, USA', 
                  'DAL': 'Dallas Mavericks, USA', 
                  'PHO': 'Phoenix Suns, USA', 
                  'NOP': 'New Orleans Pelicans, USA', 
                  'SAC': 'Sacramento Kings, USA', 
                  'LAL': 'Los Angeles Lakers, USA', 
                  'GSW': 'Golden State Warriors, USA', 
                  'HOU': 'Houston Rockets, USA', 
                  'UTA': 'Utah Jazz, USA', 
                  'MEM': 'Memphis Grizzlies, USA', 
                  'POR': 'Portland Trail Blazers, USA', 
                  'SAS': 'San Antonio Spurs, USA'}


def get_player_url(soup, player_name):
    player_url = None
    for links in soup.find_all('a'):
        if links.text == player_name:
            player_url = 'https://basketball.realgm.com/' + links.get('href')
            break
    return player_url

def get_player_age(soup2, player):
    for texts in soup2.find_all('p'):
        if 'Born' in texts.text:
            player['age'] = ' '.join(texts.text.split(' ')[4:]).replace('(', '').replace(')', '')
        if 'Hand' in texts.text:
            player['hand'] = texts.text.split(' ')[-1]
    return player

def get_player_image(soup2, player_name, player):
    for imgs in soup2.find_all('img'):
        if 'profiles' in imgs.get('src'):
            player['image'] = 'https://basketball.realgm.com/' + imgs.get('src')
            break
    if 'image' not in player:
        player['image'] = 'https://www.pngitem.com/pimgs/m/146-1468479_my-profile-icon-blank-profile-picture-circle-hd.png'
    return player

def get_national_team_info(players_table, player):
    national_table = pd.DataFrame([table for table in players_table if 'Event' in table.columns and any(table['Event'].str.contains('FIBA|World Cup|EuroBasket|Olympic|Qualifier'))][0])
    last_event = national_table.Event.tolist()[0]
    last_year_played = national_table.Year.tolist()[0]
    national_teams = len(national_table)-2 # Subtract 2 for the total and averages rows
    gp = national_table.GP.tolist()[-1]
    mins = national_table.MIN.tolist()[-2]
    player['match_info_national'] = '({} GP | {} MPG)'.format(gp, mins)
    player['national_experience'] = f'{national_teams} National Teams'
    player['last_event_played'] = f'{last_year_played} {last_event}'
    return player


def calculate_pro_years(first_nba_season, last_nba_season, first_international_season, last_international_season):
    nba_start_year = int(first_nba_season.split('-')[0])
    nba_end_year = int(last_nba_season.split('-')[0])
    international_start_year = int(first_international_season.split('-')[0])
    international_end_year = int(last_international_season.split('-')[0])
    
    start_year = min(nba_start_year, international_start_year)
    end_year = max(nba_end_year, international_end_year)
    
    pro_years = end_year - start_year + 1
    return pro_years

def get_pro_years(players_table, player, NBA_teams_dict):
    last_season_team = 'N/A'
    try:
        nba_table = [pd.DataFrame(table) for table in players_table if 'Team' in table.columns and any(table['Team'].str.contains('BOS|MIL|CLE|ORL|NYK|IND|MIA|PHI|CHI|ATL|BRK|TOR|CHO|WAS|DET|MIN|DEN|OKC|LAC|DAL|PHO|NOP|SAC|LAL|GSW|HOU|UTA|MEM|POR|SAS'))][0]
        first_nba_season = nba_table['Season'].tolist()[0]
        last_nba_season = nba_table['Season'].tolist()[-2]
        if last_nba_season == '2023-24 *':
            teams = nba_table[nba_table['Season'] == '2023-24 *']['Team'].tolist()
            last_season_team = ' - '.join([NBA_teams_dict[team] for team in teams if team in NBA_teams_dict.keys()])
    except:
        first_nba_season = '2100'
        last_nba_season = '1900'

    try:
        international_table = [pd.DataFrame(table) for table in players_table if 'League' in table.columns and not any(table['Team'].str.contains('BOS|MIL|CLE|ORL|NYK|IND|MIA|PHI|CHI|ATL|BRK|TOR|CHO|WAS|DET|MIN|DEN|OKC|LAC|DAL|PHO|NOP|SAC|LAL|GSW|HOU|UTA|MEM|POR|SAS'))][0]
        first_international_season = international_table['Season'].tolist()[0]
        last_international_season = international_table['Season'].tolist()[-1]
        if last_international_season == '2023-24 *' or last_international_season == '2023-24':
            teams = international_table[(international_table['Season'] == '2023-24 *')|(international_table['Season'] == '2023-24')]['Team'].unique().tolist()
            last_season_team = ' - '.join([team for team in teams if team != 'All Teams'])
    except:
        first_international_season = '2100'
        last_international_season = '1900'

    player['pro_years'] = f'{calculate_pro_years(first_nba_season, last_nba_season, first_international_season, last_international_season)} Years Pro'
    return player


def format_last_season(int_last_season, int=True):
    # Keep only the first row for each player
    df = int_last_season.copy()
    # Get unique team names and leagues from the other rows
    unique_teams = df[df['Team'] != 'All Teams']['Team'].unique()
    if int:
        unique_leagues = df[df['League'] != 'All Leagues']['League'].unique()
        df.loc[df['League'] == 'All Leagues', 'League'] = ', '.join(unique_leagues)

    # Replace 'All Teams' and 'All Leagues' with the unique values
    df.loc[df['Team'] == 'All Teams', 'Team'] = ', '.join(unique_teams)
    return df.drop_duplicates(subset='Player', keep='first')



def get_last_season_data(last_season_data, tables_player, player):
    nba_tables = [pd.DataFrame(table) for table in tables_player if 'Team' in table.columns and any(table['Team'].str.contains('BOS|MIL|CLE|ORL|NYK|IND|MIA|PHI|CHI|ATL|BRK|TOR|CHO|WAS|DET|MIN|DEN|OKC|LAC|DAL|PHO|NOP|SAC|LAL|GSW|HOU|UTA|MEM|POR|SAS'))]
    if len(nba_tables)>0:
        nba_table = nba_tables[0]
        nba_last_season = nba_table[(nba_table['Season'] == '2023-24 *')|(nba_table['Season']=='2023-24')|(nba_table['Season']=='2023-24 ☆')][['Team','GP', 'MIN', 'PTS', 'TRB', 'AST', 'FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'DEF', 'STL', 'BLK', 'PF', 'TOV']]
        if len(nba_last_season) >0:
            nba_last_season['Player'] = player
            nba_last_season_ = format_last_season(nba_last_season, int=False)
            last_season_data = pd.concat([last_season_data, nba_last_season_])


    international_tables = [pd.DataFrame(table) for table in tables_player if 'League' in table.columns and not any(table['Team'].str.contains('BOS|MIL|CLE|ORL|NYK|IND|MIA|PHI|CHI|ATL|BRK|TOR|CHO|WAS|DET|MIN|DEN|OKC|LAC|DAL|PHO|NOP|SAC|LAL|GSW|HOU|UTA|MEM|POR|SAS'))]
    if len(international_tables) >0:
        international_table = international_tables[0]
        int_last_season = international_table[(international_table['Season'] == '2023-24 *')|(international_table['Season']=='2023-24')][['Team', 'League','GP', 'MIN', 'PTS', 'TRB', 'AST', 'FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'DEF', 'STL', 'BLK', 'PF', 'TOV']]
        if len(int_last_season) >0:
            int_last_season['Player'] = player
            int_last_season_ = format_last_season(int_last_season)
            last_season_data = pd.concat([last_season_data, int_last_season_])
    
    return last_season_data


def get_tables(soup):
    tables = {}
    nba_career_h2 = soup.find(lambda tag: tag.name == "h2" and "NBA Regular Season Stats - Per Game" in tag.text)
    if nba_career_h2 is not None:
        nba_career = str(nba_career_h2.find_next("table"))
        nba_df = pd.read_html(nba_career)[0]
        nba_df.fillna('', inplace=True)
        tables['nba_career'] = nba_df.to_dict('records')
    else:
        tables['nba_career'] = []

    international_career_h2 = soup.find(lambda tag: tag.name == "h2" and "International Regular Season Stats - Per Game" in tag.text)
    if international_career_h2 is not None:
        international_career = str(international_career_h2.find_next("table"))
        international_df = pd.read_html(international_career)[0]
        international_df.fillna('', inplace=True)
        tables['international_career'] = international_df.to_dict('records')
    else:
        tables['international_career'] = []

    fiba_career_h2 = soup.find(lambda tag: tag.name == "h2" and "FIBA Senior Team Events Stats" in tag.text)
    if fiba_career_h2 is not None:
        fiba_career = str(fiba_career_h2.find_next("table"))
        fiba_df = pd.read_html(fiba_career)[0]
        fiba_df.fillna('', inplace=True)
        tables['fiba_career'] = fiba_df.to_dict('records')
    else:
        tables['fiba_career'] = []

    return tables



def fill_rosters_with_additional_info(rosters, country, tables, soup):
    last_season_data = pd.DataFrame()
    for continent, countries in rosters.items():
        for country_, info in countries.items():
            if country_ == country:
                table_players = [pd.DataFrame(table) for table in tables if any(table.Nationality==country_)]
                info['players']  = table_players[0].to_dict(orient="records")
                for player in info['players']:
                    player_name = player['Player']
                    player_url = get_player_url(soup, player_name)
                    if player_url:
                        response2 = requests.get(player_url)
                        if response2.status_code == 200:
                            soup2 = BeautifulSoup(response2.content, 'html.parser')
                            player_tables = pd.read_html(player_url)
                            player['tables'] = get_tables(soup2)
                            player = get_player_age(soup2, player)
                            player = get_player_image(soup2, player_name, player)
                            player = get_national_team_info(player_tables, player)
                            player = get_pro_years(player_tables, player, NBA_teams_dict)
                            last_season_data = get_last_season_data(last_season_data, player_tables, player_name)
                            if player_name in last_season_data['Player'].tolist():
                                last_team = last_season_data[last_season_data['Player'] == player_name]['Team'].tolist()[0]
                                if last_team in NBA_teams_dict.keys():
                                    player['last_season_team'] = NBA_teams_dict[last_team]
                                else:
                                    player['last_season_team'] = last_team
                            else:
                                player['last_season_team'] = 'N/A'


                    else:
                        player['age'] = 'N/A'
                        player['image'] = 'https://www.pngitem.com/pimgs/m/146-1468479_my-profile-icon-blank-profile-picture-circle-hd.png'
                        player['match_info_national'] = 'N/A'
                        player['national_experience'] = 'N/A'
                        player['last_event_played'] = 'N/A'
                        player['pro_years'] = 'N/A'
                        player['tables'] = []
                        player['last_season_team'] = 'N/A'
                if 'League' not in last_season_data.columns:
                    last_season_data['League'] = np.nan
                last_season_data = last_season_data[['Player', 'League', 'Team','GP', 'MIN', 'PTS', 'TRB', 'AST', 'FGM', 'FGA', 'FG%', '3PM', '3PA', '3P%', 'FTM', 'FTA', 'FT%', 'DEF', 'STL', 'BLK', 'PF', 'TOV']]
                last_season_data.League.fillna('NBA', inplace=True)
                last_season_data.reset_index(drop=True, inplace=True)
                # last_season_data = last_season_data.applymap(lambda x: round(x, 2) if isinstance(x, float) else x)

                info['last_season_stats'] = last_season_data.to_dict('records')
                break
    return rosters


def get_rosters(rosters, country):
    url = 'https://basketball.realgm.com/national/tournament/2/FIBA-World-Cup/318/rosters'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
    
    tables = pd.read_html(url)
    fill_rosters_with_additional_info(rosters, country, tables, soup)
    return rosters



def fix_positions(updated_rosters, country):
    for continent, countries_info in updated_rosters.items():
        players_by_pos = defaultdict(list)
        if country in countries_info:
            players_by_pos = defaultdict(list)
            positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'FC']
            positions_count = {'PG': 0, 'SG': 0, 'SF': 0, 'PF': 0, 'C': 0, 'G': 0, 'F': 0}
            for player in [pl for pl in updated_rosters[continent][country]['players'] if pl['Pos'] in positions[:5]]:
                pos = player['Pos']
                players_by_pos[pos].append(player)
                positions_count[pos] += 1
            
            for player in [pl for pl in updated_rosters[continent][country]['players'] if pl['Pos'] in positions[5:]]:
                pos = player['Pos']
                if pos == 'G':
                    if positions_count['PG'] < positions_count['SG']:
                        players_by_pos['PG'].append(player)
                        positions_count['PG'] += 1
                    elif positions_count['SG'] <= positions_count['PG']:
                        players_by_pos['SG'].append(player)
                        positions_count['SG'] += 1
                elif pos == 'F':
                    if positions_count['SF'] < positions_count['PF']:
                        players_by_pos['SF'].append(player)
                        positions_count['SF'] += 1
                    elif positions_count['PF'] <= positions_count['SF']:
                        players_by_pos['PF'].append(player)
                        positions_count['PF'] += 1
                elif pos == 'FC':
                    if positions_count['PF'] < positions_count['C']:
                        players_by_pos['PF'].append(player)
                        positions_count['PF'] += 1
                    elif positions_count['C'] <= positions_count['PF']:
                        players_by_pos['C'].append(player)
                        positions_count['C'] += 1
                else:
                    players_by_pos[pos].append(player)
                    positions_count[pos] += 1
            break
    return players_by_pos
        
position_map = {
        'PG': 'Point Guard',
        'SG': 'Shooting Guard',
        'SF': 'Small Forward',
        'PF': 'Power Forward',
        'C': 'Center'
    }
def fill_rosters(rosters):
    updated_rosters = {}
    for continent, countries in rosters.items():
        for country, info in countries.items():
            updated_rosters[country] = get_rosters(rosters, country)
            # Convert the DataFrame to a dictionary
    with open('updated_rosters.json', 'w') as f:
        json.dump(updated_rosters, f)
    return updated_rosters

# updated_rosters = fill_rosters(rosters)

# @app.route('/')
# def index():
#     # updated_rosters = get_rosters(rosters)
#     return render_template('index.html', rosters=rosters)

# @app.route('/<country>')
# def roster(country): 
#     updated_rosters = get_rosters(rosters, country)
#     players_by_pos = fix_positions(updated_rosters, country)
#     players_by_pos = dict(sorted(players_by_pos.items(), key=lambda x: ['PG', 'SG', 'SF', 'PF', 'C'].index(x[0])))
#     return render_template('rosters.html', country=country, rosters=players_by_pos, positionMap=position_map)





# # Example usage


# if __name__ == '__main__':
#     app.run(debug=True)