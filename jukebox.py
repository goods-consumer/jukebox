from gmusicapi import Mobileclient
import sys
import spotipy
import spotipy.util as util
from unidecode import unidecode
import requests
requests.packages.urllib3.disable_warnings()

def log_into_Google():
	gAccount = raw_input("Google account name:")
	gPwd = raw_input("Google password:")
	logged_in = gMusic.login(gAccount, gPwd, gMusic.FROM_MAC_ADDRESS)
	# logged_in is True if login was successful
	if logged_in:
		print("Successfully logged into Google Play Music.")
	else:
		print("Login unsuccessful.")
		sys.exit(0)

def retrieve_music_from_Google():
	gMusicSongs = gMusic.get_all_user_playlist_contents()
	charsToRemove = set(['[', ']', '(', ')', '&'])
	for playlist in gMusicSongs:
		name = playlist['name']
		songs = []
		for returnedValues in playlist['tracks']:
			if 'track' in returnedValues:
				title = filter(lambda x: x not in charsToRemove, str(returnedValues['track']['title']))
				artist = filter(lambda x: x not in charsToRemove, str(returnedValues['track']['artist']))
				duration = stuff['track']['durationMillis']
				songs.append([unidecode(title + ' ' + artist), duration])
		songs_dict[name] = songs

def log_into_Spotify():
	scope = 'playlist-modify-public'
	sID = raw_input("Spotify client id:")
	sSecret = raw_input("Spotify client secret:")
	uri = 'http://google.com'
	token = util.prompt_for_user_token(sUsername, scope, sID, sSecret, uri)
	return token

def transfer_music_to_Spotify():
	sp = spotipy.Spotify(auth=log_into_Spotify())
	print("Successfully logged into Spotify.")
	current_playlists = []
	for item in sp.user_playlists(sUsername)['items']:
		current_playlists.append(item['name'])
	current_playlists_dict = {}
	fails = [] #stores names of songs not found in Spotify
	for playlist in songs_dict:
		if playlist not in current_playlists: #avoid overwriting existing playlists
			sp.user_playlist_create(sUsername, playlist)
			for playlist in sp.user_playlists(sUsername)['items']:
				current_playlists_dict[playlist['name']] = playlist['id']
	for playlist in songs_dict:
		if playlist in current_playlists_dict:
			songs_to_add = []
			for songs in songs_dict[playlist]:
				matches = sp.search(songs[0], 20, 0, 'track')['tracks']['items'] #get top 20 matches
				length = len(matches)
				if length == 0:
					print("Song not found: " + songs[0])
					fails.append(songs[0])
				else:
					for i in range(length):
						song = matches[i]
						if abs((song['duration_ms']) - int(songs[1])) <= 1000: #compare tracks based on length
							songs_to_add.append(song['id'])
							break	
						elif i == length - 1:
							fails.append(songs[0])
			sp.user_playlist_add_tracks(sUsername, current_playlists_dict[playlist], songs_to_add)
	print("Done transferring playlists.")
	if len(fails) != 0:		
		print("Songs not found on Spotify:")		
		print(fails)

gMusic = Mobileclient()
songs_dict = {}
log_into_Google()
retrieve_music_from_Google()
sUsername = raw_input("Spotify account name:")
transfer_music_to_Spotify()
