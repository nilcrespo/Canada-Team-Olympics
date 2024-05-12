from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from models import Country, Player
from flask_sqlalchemy import SQLAlchemy

from app import app

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'  # Use the appropriate database URI for your application
db = SQLAlchemy(app)

# Initialize the admin interface
admin = Admin(app, name='myapp', template_mode='bootstrap3')

# Add views for your models
admin.add_view(ModelView(Country, db.session))
admin.add_view(ModelView(Player, db.session))
admin.add_view(ModelView(Country, db.session, category='Custom', name='Create Country'))
