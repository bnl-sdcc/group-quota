
from flask import Flask, request, render_template, redirect, url_for, make_response

from flask.ext.wtf import Form
from wtforms import TextField, SubmitField
from wtforms.validators import DataRequired


SQLALCHEMY_DATABASE_URI = 'mysql://willsk@localhost/group_quotas'

app = Flask(__name__)

app.config.from_object(__name__)
app.config.from_envvar('CCFGDIST_CFG', silent=True)
app.config['APPLICATION_ROOT'] = '/farmapp/'

from database import db_session
from models import Group


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def menu():
    groups = Group.query.all()
    print groups

    return render_template('group_view.html', groups=groups)

# if __name__ == '__main__':
#     app.run(debug=True)