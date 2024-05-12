from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    flag = db.Column(db.String(200), nullable=False)
    players = db.relationship('Player', backref='country', lazy=True)
    
    def __repr__(self):
        return f"Country('{self.name}', '{self.flag}')"

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(20), nullable=True)
    image = db.Column(db.String(200), nullable=True)
    match_info_national = db.Column(db.String(100), nullable=True)
    national_experience = db.Column(db.String(100), nullable=True)
    last_event_played = db.Column(db.String(100), nullable=True)
    pro_years = db.Column(db.String(20), nullable=True)
    last_season_team = db.Column(db.String(100), nullable=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)