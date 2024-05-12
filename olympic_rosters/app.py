import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from flask_caching import Cache
from collections import defaultdict
from flask import Flask, render_template, abort

from auxiliar_fns import fix_positions, position_map, get_rosters, rosters, get_continent

app = Flask(__name__)


@app.route('/')
def index():
    # updated_rosters = get_rosters(rosters)
    return render_template('index.html', rosters=rosters)

cache = Cache(config={'CACHE_TYPE': 'simple'})
cache.init_app(app)

# @app.route('/<country>')
# def roster(country): 
#     for continent, countries in rosters.items():
#         for country_, info in countries.items():
#             if country == country_:
#                 updated_rosters = get_cached_rosters(country)
#                 players_by_pos = fix_positions(updated_rosters, country)
#                 players_by_pos = dict(sorted(players_by_pos.items(), key=lambda x: ['PG', 'SG', 'SF', 'PF', 'C'].index(x[0])))
#                 last_season_data = updated_rosters[get_continent(country)][country]['last_season_stats']
#                 return render_template('rosters.html', country=country, rosters=players_by_pos, positionMap=position_map, last_season_data=last_season_data)

@app.route('/<country>')
def roster(country):
    with open('../updated_rosters.json', 'r') as f:
        updated_rosters = json.load(f)
    # Convert the dictionary back to a DataFrame
    players_by_pos = fix_positions(updated_rosters[country], country)
    players_by_pos = dict(sorted(players_by_pos.items(), key=lambda x: ['PG', 'SG', 'SF', 'PF', 'C'].index(x[0])))
    last_season_data = pd.DataFrame(updated_rosters[country][get_continent(country)][country]['last_season_stats'])
    return render_template('rosters.html', country=country, rosters=players_by_pos, positionMap=position_map, last_season_data=last_season_data)

# @app.route('/<country>/<player_name>')
# def player(country, player_name):
#     updated_rosters = get_cached_rosters(country)
#     # Find the player in the rosters
#     for player in updated_rosters[get_continent(country)][country]['players']:
#         if player['Player'] == player_name:
#             # Pass the player's data to the template
#             all_tables = player['tables']
#             print(all_tables)
#             return render_template('player.html', player=player, tables = all_tables)
#     # If the player was not found, return a 404 error
#     abort(404)

@app.route('/<country>/<player_name>')
def player(country, player_name):
    with open('../updated_rosters.json', 'r') as f:
        updated_rosters = json.load(f)
    # Find the player in the rosters
    for player in updated_rosters[country][get_continent(country)][country]['players']:
        if player['Player'] == player_name:
            # Pass the player's data to the template
            all_tables = player['tables']
            return render_template('player.html', player=player, tables = all_tables, country=country)
    # If the player was not found, return a 404 error
    abort(404)


@app.route('/favicon.ico')
def favicon():
    return "No favicon", 404

@cache.memoize(timeout=60*60*24)  # Cache results for 24 hours
def get_cached_rosters(country):
    return get_rosters(rosters, country)




# Example usage


if __name__ == '__main__':
    app.run(debug=True)