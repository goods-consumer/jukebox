import requests
import soundcloud
import spotipy

from flask import Flask, render_template, redirect, request, session, url_for, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from copy import deepcopy

SPOTIPY_CLIENT_ID=""
SPOTIPY_CLIENT_SECRET=""

app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secret"

soundcloud = soundcloud.Client(
    client_id="",
    client_secret="",
    redirect_uri='http://127.0.0.1:5000/sccallback'
)


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login-form")
def login():
    parameters = [
        "client_id={}".format(SPOTIPY_CLIENT_ID),
        "redirect_uri={}".format("http://127.0.0.1:5000/spcallback"),
        "response_type=code",
        "scope=playlist-modify-public playlist-modify-private"
        ]
    sp_url = "https://accounts.spotify.com/authorize?"
    sp_url += "&".join(parameters)
    return redirect(sp_url)


@app.route("/spcallback")
def spcallback():
    # POST code from Spotify redirect to get access token
    code = request.args.get("code")
    error = request.args.get("error")
    if error:
        return("Error! {}".format(error))
    # exchange code for an access token
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    data = {
        "client_id": SPOTIPY_CLIENT_ID,
        "client_secret":SPOTIPY_CLIENT_SECRET,
        "redirect_uri": "http://127.0.0.1:5000/spcallback",
        "code": code,
        "grant_type": "authorization_code"
    }
    r = requests.post(TOKEN_URL, data=data)
    token = r.json().get("access_token")
    if token:
        session["token"] = token
        return redirect(soundcloud.authorize_url())
    return render_template('error.html')

    
@app.route("/sccallback")
def sccallback():
    client_token = soundcloud.exchange_token(code=request.args.get('code')).fields()
    access_token = client_token["access_token"]
    scope = client_token["scope"]
    sc_playlists = soundcloud.get('/me/playlists')
    return render_template('playlists.html', playlists = [p.title for p in sc_playlists])


@app.route("/sc_to_sp", methods=['POST'])
def sc_to_sp():
    sc_playlists_list = soundcloud.get('/me/playlists')
    sc_playlists = {}
    for pl in sc_playlists_list:
        sc_playlists[pl.title] = pl
    spotify = spotipy.Spotify(session["token"])
    user_id = spotify.current_user().get('id')
    selected_playlists = request.form.getlist('playlists')
    fails = {}
    for pl in selected_playlists:
        playlist = sc_playlists[str(pl)]
        fails[playlist.title] = []
        songs_to_add = []
        for track in playlist.tracks:
            title = track['title']
            artist = track['user']['username']
            duration = track['duration']
            matches = spotify.search('{} {}'.format(title, artist))['tracks']['items']
            if not len(matches):
                matches = spotify.search(title)['tracks']['items']
                # if not len(matches):
                #     print ("No match for {}, {}.".format(title, artist))
            success = False
            for match in matches:
                if abs(match['duration_ms'] - duration) <= 1321:
                    # print ('{}, {}'.format(match['name'], match['artists'][0]['name']))
                    songs_to_add.append(match['id'])
                    success = True
                    break
            if not success:
                fails[playlist.title].append(title)
        if len(songs_to_add):
            playlist_id = spotify.user_playlist_create(user_id, playlist.title)['id']
            spotify.user_playlist_add_tracks(user_id, playlist_id, songs_to_add)
        # else:
        #     print ('No matches found.')
    for key in deepcopy(fails):
        if not len(fails[key]):
            fails.pop(key)
    # return jsonify(fails)
    return render_template('fails.html', fails = fails)

if __name__ == "__main__":
    # app.debug = True
    # DebugToolbarExtension(app)
    app.run()
