import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from collections import defaultdict

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

def get_rosters(rosters, country):
    url = 'https://basketball.realgm.com/national/tournament/2/FIBA-World-Cup/318/rosters'
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
    
    tables = pd.read_html(url)
    for continent, countries in rosters.items():
        for country_, info in countries.items():
            if country_ == country:
                table_players = [pd.DataFrame(table) for table in tables if any(table.Nationality==country_)]
                info['players']  = table_players[0].to_dict(orient="records")
                for player in info['players']:
                    player_name = player['Player']
                    player_url = None
                    for links in soup.find_all('a'):
                        if links.text == player_name:
                            player_url = 'https://basketball.realgm.com/' + links.get('href')
                            break
                    if player_url:
                        response2 = requests.get(player_url)
                        if response2.status_code == 200:
                            soup2 = BeautifulSoup(response2.content, 'html.parser')
                            for imgs in soup2.find_all('img'):
                                if player_name.split(' ')[1] in imgs.get('src'):
                                    player['image'] = 'https://basketball.realgm.com/' + imgs.get('src')
                                    break
    return rosters

def process_roster_data(roster):
    positions = ['PG', 'SG', 'SF', 'PF', 'C', 'G', 'F', 'FC', 'GF']
    players_by_pos = defaultdict(list)
    positions_count = {'PG': 0, 'SG': 0, 'SF': 0, 'PF': 0, 'C': 0, 'G': 0, 'F': 0, 'FC':0, 'GF':0}

    for player in roster['players']:
        st.write(player)
        pos = player['Pos']
        players_by_pos[pos].append(player)
        positions_count[pos] += 1

    for player in [pl for pl in roster['players'] if pl['Pos'] in positions[5:]]:
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
        elif pos == 'GF':
            if positions_count['SG'] < positions_count['SF']:
                players_by_pos['SG'].append(player)
                positions_count['SG'] += 1
            elif positions_count['SF'] <= positions_count['SG']:
                players_by_pos['SF'].append(player)
                positions_count['SF'] += 1
        else:
            players_by_pos[pos].append(player)
            positions_count[pos] += 1
    st.write(positions_count)
    st.write(players_by_pos)
    players_by_pos = dict(sorted(players_by_pos.items(), key=lambda x: ['PG', 'SG', 'SF', 'PF', 'C', 'F', 'G', 'FC','GF'].index(x[0])))
    players_by_pos.pop('FC', None)
    players_by_pos.pop('G', None)
    players_by_pos.pop('F', None)
    return players_by_pos

def set_page_config(page_title, page_icon):
    st.set_page_config(
        page_title=page_title,
        page_icon=page_icon,
        layout="wide",
        initial_sidebar_state="expanded",
    )

def main():
    set_page_config("Olympic Basketball Rosters 2024", ":trophy:")
    columns = st.columns([2,4,2])
    with columns[0]:
        pass  # Add code to display the flag image

    with columns[1]:
        st.title("Olympic Basketball Rosters 2024")
        continent_options = rosters.keys()
        for continent in continent_options:
            st.markdown(f"## **{continent}**")
            countries = [country for country in rosters[continent].keys()]
            for country in countries:
                with st.expander(f"{country} Roster"):
                    updated_rosters = get_rosters(rosters, country)
                    players_by_pos = process_roster_data(updated_rosters[continent][country])
                    st.write(players_by_pos)

    with columns[2]:
        pass  # Add code to display additional information or widgets
    # continent_options = rosters.keys()
    # for continent in continent_options:
    #     st.markdown(f"## **{continent}**")
    #     countries = [country for country in rosters[continent].keys()]
    #     for country in countries:
    #         # if st.button(f":flag_{country.lower()}: {country}", key=country):
    #         with st.expander(f"{country} Roster"):
    #             updated_rosters = get_rosters(rosters, country)
    #             # flag_url = updated_rosters[continent][country]['flag']
    #             # html = f"<a href='{flag_url}'><img src='{flag_url}'></a>"
    #             # st.markdown(html, unsafe_allow_html=True)
    #             players_by_pos = process_roster_data(updated_rosters[continent][country])
    #             st.write(players_by_pos)
    # continent = st.selectbox("Select a continent", continent_options)

    # if continent:
    #     st.subheader(f"{continent} Rosters")
    #     countries = [country for country in rosters[continent].keys()]
    #     country = st.selectbox("Select a country", countries)

    #     if country:
    #         updated_rosters = get_rosters(rosters, country)
    #         flag_url = updated_rosters[continent][country]['flag']
    #         st.image(flag_url, use_column_width=True)
    #         players_by_pos = process_roster_data(updated_rosters[continent][country])
    #         st.write(players_by_pos)

if __name__ == "__main__":
    main()

