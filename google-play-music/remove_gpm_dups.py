#!/usr/bin/env python
#
# Utility to remove duplicates within all songs in Google Play Music
# using gmusicapi, the unofficial API for Google Play Music.
#
# Bhupendra Bhudia, 7th April 2016
#
# Improvements based on excerpts and sourced from:
# - git@github.com:maxkirchoff/google-music-dupe-killer.git
# - git@github.com:hausfrau87/GoogleMusicPlaylistFixer.git
# - git@github.com:kennyszub/google-music-playlist-scripts.git
#

import sys

import argparse
from gmusicapi import Mobileclient


class GoogleMusicDuplicateManager(object):
    """
    Utility manager to remove duplicate songs across library and playlists in Google Play Music
    using gmusicapi, the unofficial API for Google Play Music.
    """

    def __init__(self, argv):

        self.argv = argv

    def validate_args(self):
        """
        Parse and validate command line arguments
        :return: args dictionary from argument parser
        """

        parser = argparse.ArgumentParser()

        parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
        parser.add_argument("-u", "--user", help="Google user email", default="none")
        parser.add_argument("-p", "--password", help="Google user email password", default="none")
        parser.add_argument("-l", "--library", help="Remove duplicate songs from library", action="store_true")
        parser.add_argument("-y", "--playlist", help="Remove duplicate songs from playlists", action="store_true")
        # Built-in:
        # parser.add_argument("-h", "--help", help="Usage help", action="store_true")

        args = parser.parse_args()
        if len(self.argv) == 0 or args.user == "none" or args.password == "none" or not (args.library or args.playlist):
            parser.print_help()
            exit(0)

        return args

    def run(self):
        """
        Parse and validate command line arguments and then run the necessary playlist and/or library duplicates checker and remover.
        :return:
        """

        args = self.validate_args()
        self.user = args.user

        client = Mobileclient()
        logged_in = client.login(args.user, args.password, Mobileclient.FROM_MAC_ADDRESS)

        if not logged_in:
            print "Failed to login to Google Play Music"
            exit(1)

        if args.playlist:
            self.remove_playlist_dups(client)

        if args.library:
            self.remove_library_dups(client)

    def remove_playlist_dups(self, client):
        """
        Find and remove duplicate songs from all playlists
        :param client: Mobileclient for gmusicapi
        :return:
        """

        print "\n\nGetting all Google Play Music playlist contents for '%s'..." % (self.user)
        playlists = client.get_all_user_playlist_contents()
        print "\n"

        num_playlists = len(playlists)
        playlist_count = 1
        for playlist in playlists:
            print "%d/%d#: Checking for duplicates within '%s'..." % (playlist_count, num_playlists, playlist['name'].encode('utf-8'))
            tracks = playlist['tracks']

            # Identify duplicates within this playlist...
            track_set = set()
            dup_entry_ids = []
            for track in tracks:
                track_id = track['trackId']
                if track_id in track_set:
                    print "    Found duplicate with trackId: %s" % (track_id)
                    dup_entry_ids.append(track['id'])
                else:
                    track_set.add(track_id)

            if len(dup_entry_ids) > 0:
                print "    ==> *** REMOVING %d DUPLICATES *** <==" % (len(dup_entry_ids))
                client.remove_entries_from_playlist(dup_entry_ids)
            else:
                print "    ==> No duplicates found <=="

            playlist_count += 1

        print "Processed all %d playlists" % (num_playlists)

    def remove_library_dups(self, client):
        """
        Find and remove duplicate songs from the library
        :param client: Mobileclient for gmusicapi
        :return:
        """

        print "\n\nGetting all Google Play Music library contents for '%s'..." % (self.user)
        all_songs = client.get_all_songs()
        print "\n"

        new_songs = {}
        old_songs = {}
        print "Checking for duplicates..."
        for song in all_songs:
            song_id = song.get('id')
            timestamp = song.get('recentTimestamp')

            key = "%s: %d-%02d %s" % (song.get('album'), song.get('discNumber'), song.get('trackNumber'), song.get('title'))

            # Identify duplicates within this library...
            if key in new_songs:
                if new_songs[key]['timestamp'] < timestamp:
                    old_songs[key] = new_songs[key]
                    new_songs[key] = {'id': song_id, 'timestamp': timestamp}
                else:
                    old_songs[key] = {'id': song_id, 'timestamp': timestamp}

            new_songs[key] = {'id': song_id, 'timestamp': timestamp}

        if len(old_songs):
            print "Found duplicate songs"

            old_song_ids = []
            for key in sorted(old_songs.keys()):
                old_song_ids.append(old_songs[key]['id'])
                print "    ==> %s <==" % (key.encode('utf-8'))

            print "Deleting duplicate songs..."
            client.delete_songs(old_song_ids)
        else:
            print "No duplicate songs"

        print "Processed all %d songs" % (len(all_songs))


def main(argv):
    dup_checker = GoogleMusicDuplicateManager(argv)
    dup_checker.run()


if __name__ == "__main__":
    main(sys.argv)
