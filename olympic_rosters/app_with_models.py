from flask import Flask, render_template, abort, request, redirect, url_for
import requests
from collections import defaultdict
from bs4 import BeautifulSoup
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from models import Country, Player
from olympic_rosters.auxiliar_fns import fix_positions, get_rosters, rosters

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///olympic_rosters.db'
db = SQLAlchemy(app)

@app.route('/')
def index():
    countries = Country.query.all()
    return render_template('index.html', countries=countries)

@app.route('/<country>')
def roster(country):
    updated_rosters = get_rosters(rosters, country)
    fill_models(updated_rosters)
    country_obj = Country.query.filter_by(name=country).first()
    if country_obj:
        players = country_obj.players
        players_by_pos = fix_positions(players)
        return render_template('rosters.html', country=country, rosters=players_by_pos, positionMap=position_map)
    else:
        abort(404)

@app.route('/create_country', methods=['GET', 'POST'])
def create_country():
    if request.method == 'POST':
        name = request.form['name']
        flag = request.form['flag']
        new_country = Country(name=name, flag=flag)
        db.session.add(new_country)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('create_country.html')


position_map = {
    'PG': 'Point Guard',
    'SG': 'Shooting Guard',
    'SF': 'Small Forward',
    'PF': 'Power Forward',
    'C': 'Center'
}

def fill_models(rosters):
    for continent, countries in rosters.items():
        for country_name, country_info in countries.items():
            country = Country(name=country_name, flag=country_info['flag'])
            db.session.add(country)
            db.session.commit()
            for player in country_info['players']:
                player_obj = Player(name=player['Player'], age=player.get('age', 'N/A'), 
                                    image=player.get('image', 'https://www.pngitem.com/pimgs/m/146-1468479_my-profile-icon-blank-profile-picture-circle-hd.png'), 
                                    match_info_national=player.get('match_info_national', 'N/A'), 
                                    national_experience=player.get('national_experience', 'N/A'), 
                                    last_event_played=player.get('last_event_played', 'N/A'), 
                                    pro_years=player.get('pro_years', 'N/A'), 
                                    last_season_team=player.get('last_season_team', 'N/A'), 
                                    country=country)
                db.session.add(player_obj)
    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)