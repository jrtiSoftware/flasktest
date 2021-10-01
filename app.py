# Jared Tauler 10/1/21

import os
import yaml

import pathlib
import random
import websocket as websocket

from flask import Flask, abort, redirect, request, redirect, url_for, render_template, request, session
from flask_session import Session
import flask_socketio as io
from flask_sqlalchemy import SQLAlchemy

# from flask_talisman import Talisman

from google_api_handler import GoogleSession, GmailResource

exec(open("debug.py", "r").read())

with open("config.yaml", "r") as f:
	cfg = yaml.safe_load(f)
DBstr = cfg["DBstr"]

app = Flask(__name__)
app.secret_key = os.urandom(16)
db = SQLAlchemy(app)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SQLALCHEMY_DATABASE_URI'] = DBstr
app.config["SESSION_SQLALCHEMY"] = db
socketio = io.SocketIO(app, manage_session=False)
sess = Session(app)
# Talisman(app)
GSess = GoogleSession()

# TESTING
#############################
from sqlalchemy import create_engine
# # Try reading sessions table. Create one if it isnt there.
try:
    c = create_engine(DBstr)
    c.execute("SELECT * FROM `sessions`")
except:
    db.create_all()
#
# # with open("google.yaml", "w") as f:
# #     yaml.dump({"db": scopes, "google_client_id": "21", "redirect_uri": "adsd"}, f)

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1' # For testing only!
#############################



# Main Program
@app.route('/', methods = ["GET", "POST"])
@app.route('/login', methods = ["GET", "POST"])
def login():
	# TODO make sure address right, this wont cut it.
	if request.url != "http://localhost:5000/":
		return redirect("http://localhost:5000/")

	if "google_id" in session:
		return redirect(url_for("home"))
	else:
		# This generates the authorization URL and emits it back to client for redirecting.
		print(session)
		if request.method == "GET":
			return render_template("login.html")

		else:
			authorization_url, state = GSess.flow.authorization_url()
			session["state"] = state
			return redirect(authorization_url)


@app.route("/home", methods = ["GET", "POST"])
def home():
	if "google_id" not in session:
		return abort(401)  # Authorization required
	else:
		# Get some userinfo for the page.
		with GmailResource(session["credentials"]) as resource:
			response = resource.users().getProfile(userId=session["google_id"]).execute()
		return render_template("home.html", data=response)


# After the Google login thingy,
@app.route("/callback", methods = ["GET", "POST"])
def callback():
	print(session["state"], request.args["state"])
	if not session["state"] == request.args["state"]:
		abort(500)  # State does not match!

	id_info, credentials = GSess.CreateCredentials(request)

	session["google_id"] = id_info.get("sub")
	session["name"] = id_info.get("name")

	# Make services. I honestly don't know if this is a good way of doing it or not. Keeping track of credentials and
	# building a service every time i need to use it seems like unnecessary work.
	session["credentials"] = credentials
	return redirect(url_for("home"))

@socketio.event
def Snippet():
	# Get a list of some emails.
	with GmailResource(session["credentials"]) as resource:
		response = resource.users().messages().list(
			userId=session["google_id"],
			maxResults=500
		).execute()

		# Pick one.
		choice = random.choice(response["messages"])

		# Fetch metadata for it
		response = resource.users().messages().get(
			userId=session["google_id"],
			id=choice["id"],
			format="minimal"
		).execute()

	# Return snippet of the email. I was going to be fancy and render the email in a
	# frame originally, but it seemed too hard.
	data = []
	data.append({"id": "snippetdisplay", "text": response["snippet"]})
	data.append({"id": "snippetbutton", "text": "Get snippet"})
	io.emit("UpdateElem", data)


# Logout
@socketio.event
def SessionClear():
    session.clear()
    io.emit("redirect", url_for("login"))

# Start
if __name__ == '__main__':
	# TODO certificates.
	app.run(debug=True)

