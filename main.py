#!/usr/bin python3
#!/usr/bin/env python3

import logging
import os
import sys
from bottle import Bottle, run, route, template, TEMPLATE_PATH, error, static_file, redirect, request
import datetime
import spotipy
import spotipy.util
from spotipy import oauth2
from spotipy.oauth2 import SpotifyClientCredentials


app = Bottle()

# globals
logging.basicConfig(level = logging.DEBUG, format = "%(asctime)s - %(levelname)s - %(message)s")
CLIENT_ID     = "e29426dfb22c41cdbc92122fbb9c398c"
CLIENT_SECRET = "837fd2824bec47e5a003419165674bdd"
SCOPE = "user-top-read"
CACHE = ".spotifyoauthcache"
CLIENT_CREDENTIALS = SpotifyClientCredentials(client_id = CLIENT_ID, client_secret = CLIENT_SECRET)
SP_OAUTH2 = oauth2.SpotifyOAuth(client_id = CLIENT_ID, client_secret = CLIENT_SECRET, redirect_uri = "http://localhost:8000/verified", scope = SCOPE, cache_path = CACHE)
spotify = spotipy.Spotify(client_credentials_manager = CLIENT_CREDENTIALS)
TEMPLATE_PATH.insert(0, "")

def get_token():
	access_token = ""
	token_info = SP_OAUTH2.get_cached_token()
	if token_info:
		access_token = token_info["access_token"]
	else:
		url = request.url
		code = SP_OAUTH2.parse_response_code(url)
		if code:
			print("Found Spotify auth code in Request URL! "
				"Trying to get valid access token...")
			token_info = SP_OAUTH2.get_access_token(code)
			access_token = token_info["access_token"]

	logging.debug("access_token = {}".format(access_token))
	return access_token

def getSPOauthURI():
    auth_url = SP_OAUTH2.get_authorize_url()
    return auth_url



# Static Routes
@app.route("/static/css/<filepath:re:.*\.css>")
def css(filepath):
    return static_file(filepath, root="static/css")

@app.route("/static/font/<filepath:re:.*\.(eot|otf|svg|ttf|woff|woff2?)>")
def font(filepath):
    return static_file(filepath, root="static/font")

@app.route("/static/img/<filepath:re:.*\.(jpg|jpeg|png|gif|ico|svg)>")
def img(filepath):
    return static_file(filepath, root="static/img")

@app.route("/static/js/<filepath:re:.*\.js>")
def js(filepath):
    return static_file(filepath, root="static/js")

# web interface

@app.route("/")
def root():
	if os.path.exists(CACHE):
		os.unlink(CACHE)
	htmlLoginButton = getSPOauthURI()
	return template("index.html", year = datetime.datetime.now().year, link = htmlLoginButton, search = "")

@app.route("/", method = "POST")
def get_results():
	redirect("/search/" + request.forms.get("search"))
	search(request.forms.get("search"))

@app.route("/search/<keyword>")
def search(keyword):
	logging.debug("Running search({})".format(keyword))
	result = spotify.search(q = keyword, limit = 10)
	return template("search.html", result = result, year = datetime.datetime.now().year)

@app.route("/verified")
def verify():
	if get_token():
		redirect("/most_played")

@app.route("/most_played")
def get_most_played():
	spotify = spotipy.Spotify(auth = get_token())
	spotify.trace = False
	logging.debug("Running get_most_played()")

	short_term_artists = spotify.current_user_top_artists(time_range = "short_term", limit = 100)["items"]
	short_term_tracks = spotify.current_user_top_tracks(time_range = "short_term", limit = 50)["items"]
	medium_term_artists = spotify.current_user_top_artists(time_range = "medium_term", limit = 100)["items"]
	medium_term_tracks = spotify.current_user_top_tracks(time_range = "medium_term", limit = 50)["items"]
	long_term_artists = spotify.current_user_top_artists(time_range = "long_term", limit = 100)["items"]
	long_term_tracks = spotify.current_user_top_tracks(time_range = "long_term", limit = 50)["items"]
	return template("most_played.html", spotify = spotify, short_term_artists = short_term_artists, short_term_tracks = short_term_tracks, medium_term_artists = medium_term_artists, medium_term_tracks = medium_term_tracks, long_term_artists = long_term_artists, long_term_tracks = long_term_tracks, year = datetime.datetime.now().year)

"""
	TODO: make playlist based on filter values and data shown.
"""

# error pages
@app.error(404)
def error_page(error):
	return template("error.html")

if __name__ == "__main__":
	run(app = app, host = "localhost", port = 8000, debug = True, reloader = True)
