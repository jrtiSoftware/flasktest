import os
import yaml

import pathlib
import random
import websocket as websocket

from flask import Flask, abort, redirect, request, redirect, url_for, render_template, request, session
from flask_session import Session
import flask_socketio as io
from flask_sqlalchemy import SQLAlchemy
from googleapiclient.discovery import build
# from flask_talisman import Talisman

from google_api_handler import GoogleSession

with open("config.yaml", "r") as f:
	cfg = yaml.safe_load(f)
DBstr = cfg["DBstr"]

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # For testing only!

# print(scopes)
app = Flask(__name__)
app.secret_key = os.urandom(16)
db = SQLAlchemy(app)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = DBstr
app.config["SESSION_SQLALCHEMY"] = db
socketio = io.SocketIO(app, manage_session=False)
sess = Session(app)
# Talisman(app)

TempNameAPI = GoogleSession()



# Main Program
@app.route('/', methods = ["GET", "POST"])
def login():
	authorization_url, state = TempNameAPI.flow.authorization_url()
	session["state"] = state
	print(session)
	return redirect(authorization_url)

# After the Google login thingy,
@app.route("/callback", methods = ["GET", "POST"])
def callback():
	print(session["state"], request.args["state"])
	if not session["state"] == request.args["state"]:
		abort(500)  # State does not match!

	id_info, credentials = TempNameAPI.CreateCredentials(request, session)

	session["google_id"] = id_info.get("sub")
	session["name"] = id_info.get("name")

	# Make services. I honestly don't know if this is a good way of doing it or not. Keeping track of credentials and
	# building a service every time i need to use it seems like unnecessary work.
	session["service"] = {}
	session["service"]["gmail"] = {"serviceName": 'gmail', "version": 'v1', "credentials": credentials}
	resource = build(**session["service"]["gmail"])
	response = resource.users().getProfile(userId=session["google_id"]).execute()
	return response

# Start
if __name__ == '__main__':
	# TODO certificates.
	app.run(debug=True)

