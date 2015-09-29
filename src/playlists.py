# Copyright (c) 2014-2015 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import GLib, GObject

import os
from gettext import gettext as _
import itertools
import sqlite3
from datetime import datetime

from lollypop.define import Lp


class Playlists(GObject.GObject):
    """
        Playlists manager
    """
    LOCAL_PATH = os.path.expanduser("~") + "/.local/share/lollypop"
    DB_PATH = "%s/playlists.db" % LOCAL_PATH
    __gsignals__ = {
        # Add or remove a playlist
        'playlists-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        # Objects added/removed to/from playlist
        'playlist-changed': (GObject.SignalFlags.RUN_FIRST, None, (int,))
    }
    create_playlists = '''CREATE TABLE playlists (
                            id INTEGER PRIMARY KEY,
                            name TEXT NOT NULL,
                            mtime BIGINT NOT NULL'''

    create_tracks = '''CREATE TABLE tracks (
                        id INTEGER PRIMARY KEY,
                        playlist_id INT NOT NULL,
                        track_id INT NOT NULL,
                        path TEXT NOT NULL)'''

    def __init__(self):
        """
            Init playlists manager
        """
        GObject.GObject.__init__(self)
        self._LOVED = _("Loved tracks")
        self._ALL = "@@@ALL@@@"
        self._index = 0
        self._playlists = {}

        self._sql = self.get_cursor()
        # Create db schema
        try:
            self._sql.execute(self.create_playlists)
            self._sql.execute(self.create_tracks)
        except Exception as e:
            print("Playlists::__init__(): %s" % e)

    def add(self, name, sql=None):
        """
            Add a playlist
            @param playlist name as str
            @thread safe
        """
        if not sql:
            sql = self._sql
        sql.execute("INSERT INTO playlists "
                    "VALUES (?, ?)",
                    (name, datetime.now().strftime('%s')))
        sql.commit()
        GLib.idle_add(self.emit, 'playlists-changed')

    def exists(self, name, sql=None):
        """
            Return True if playlist exist
            @param playlist name as string
            @param exist as bool
        """
        if not sql:
            sql = self._sql
        result = sql.execute("SELECT name\
                              FROM playlists\
                              WHERE name=?",
                             (name,))
        v = result.fetchone()
        if v:
            return v[0] > 1
        return False

    def rename(self, new_name, old_name, sql=None):
        """
            Rename playlist (Thread safe)
            @param new playlist name as str
            @param old playlist name as str
        """
        if not sql:
            sql = self._sql
        sql.execute("UPDATE playlists\
                    SET name=?\
                    WHERE name=?",
                    (new_name, old_name))
        sql.commit()

    def delete(self, name, sql=None):
        """
            delete playlist (Thread safe)
            @param playlist name as str
        """
        if not sql:
            sql = self._sql
        sql.execute("DELETE FROM playlists\
                    WHERE name=?",
                    (name,))
        sql.commit()

    def get(self, sql=None):
        """
            Return availables playlists
            @return array of (id, string)
        """
        if not sql:
            sql = self._sql
        result = sql.execute("SELECT rowid, name\
                              FROM playlists")
        return list(itertools.chain(*result))

    def get_last(self, sql=None):
        """
            Return 6 last modified playlist
            @return [string]
        """
        if not sql:
            sql = self._sql
        result = sql.execute("SELECT rowid, name\
                              FROM playlists\
                              ORDER BY mtime\
                              LIMIT 6")
        return list(itertools.chain(*result))

    def get_tracks(self, name, sql_l=None, sql_p=None):
        """
            Return availables tracks for playlist
            If playlist name == self._ALL, then return all tracks from db
            @param playlist name as str
            @return array of paths as [str]
        """
        if not sql_p:
            sql_p = self._sql_p
        if not sql_l:
            sql_l = self._sql_l
        if name == self._ALL:
            return Lp.tracks.get_paths(sql_l)
        else:
            result = sql_p.execute("SELECT path\
                                   FROM playlists, tracks\
                                   WHERE playlist_id=playlists.rowid\
                                   AND name=?", (name,))
            return list(itertools.chain(*result))

    def get_tracks_id(self, name, sql_l=None, sql_p=None):
        """
            Return availables tracks id for playlist
            If playlist name == self._ALL, then return all tracks from db
            @param playlist name as str
            @return array of track id as int
        """
        if not sql_l:
            sql_l = Lp.sql
        if not sql_p:
            sql_p = self._sql
        if name == self._ALL:
            return Lp.tracks.get_ids(sql_l)
        else:
            result = sql_p.execute("SELECT track_id\
                                   FROM playlists, tracks\
                                   WHERE playlist_id=playlists.rowid\
                                   AND name=?", (name,))
            return list(itertools.chain(*result))

    def clear(self, name, sql=None):
        """
            Clear playlsit
            @param playlist name as str
        """
        if not sql:
            sql = self._sql
        sql.execute("DELETE FROM tracks\
                     WHERE EXISTS (SELECT * from playlists\
                                   WHERE playlists.rowid=tracks.playlist_id)")
        sql.commit()

    def add_track(self, playlist_id, track, sql=None):
        """
            Add track to playlist if not already present
            @param playlist id as int
            @param track as Track
        """
        if not sql:
            sql = self._sql
        sql.execute("INSERT INTO tracks"
                    "VALUES (?, ?, ?)",
                    (playlist_id, track.id, track.path))
        sql.commit()
        GLib.idle_add(self.emit, "playlist-changed", playlist_id)

    def add_tracks(self, playlist_id, tracks, sql=None):
        """
            Add tracks to playlist if not already present
            @param playlist id as int
            @param tracks as [Track]
        """
        if not sql:
            sql = self._sql
        for track in tracks:
            sql.execute("INSERT INTO tracks"
                        "VALUES (?, ?, ?)",
                        (playlist_id, track.id, track.path))
        sql.commit()
        GLib.idle_add(self.emit, "playlist-changed", playlist_id)

    def remove_tracks(self, name, paths, sql=None):
        """
            Remove tracks from playlist
            @param playlist name as str
            @param paths as [str]
        """
        if not sql:
            sql = self._sql
        for path in paths:
            sql.execute("DELETE FROM tracks\
                         WHERE path=?\
                         AND EXISTS (SELECT * from playlists\
                          WHERE playlists.rowid=tracks.playlist_id)", (path,))
        sql.commit()
        GLib.idle_add(self.emit, "playlist-changed", name)

    def is_present(self, playlist_name, object_id,
                   genre_id, is_album, sql_l=None, sql_p=None):
        """
            Return True if object_id is already present in playlist
            @param playlist name as str
            @param object id as int
            @param genre id as int
            @param is an album as bool
            @param sql as sqlite cursor
            @return bool
        """
        if not sql_l:
            sql_l = Lp.sql
        if not sql_p:
            sql_p = self._sql
        paths = self.get_tracks(playlist_name, sql_p)
        if is_album:
            tracks_paths = Lp.albums.get_tracks_paths(object_id,
                                                      genre_id,
                                                      sql_l)
        else:
            tracks_paths = [Lp.tracks.get_path(object_id, sql_l)]

        found = 0
        len_tracks = len(tracks_paths)
        for filepath in tracks_paths:
            if filepath in paths:
                found += 1
                if found >= len_tracks:
                    break
        if found == len_tracks:
            return True
        else:
            return False

#######################
# PRIVATE             #
#######################
    def get_cursor(self):
        """
            Return a new sqlite cursor
        """
        try:
            return sqlite3.connect(self.DB_PATH, 600.0)
        except:
            exit(-1)


class RadiosManager(Playlists):
    """
        Radios manager
    """
    DB_PATH = "%s/radios.db" % Playlists.LOCAL_PATH

    def __init__(self):
        """
            Init radio manager
        """
        Playlists.__init__(self)
