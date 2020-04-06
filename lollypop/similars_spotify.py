# Copyright (c) 2014-2020 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from time import sleep
from random import choice, shuffle
import json

from lollypop.logger import Logger
from lollypop.define import App
from lollypop.utils import emit_signal
from lollypop.helper_task import TaskHelper
from lollypop.helper_web_spotify import SpotifyWebHelper


class SpotifySimilars(SpotifyWebHelper):
    """
        Search similar artists with Spotify
    """
    def __init__(self):
        """
            Init provider
        """
        SpotifyWebHelper.__init__(self)

    def load_similars(self, artist_ids, storage_type, cancellable):
        """
            Load similar artists for artist ids
            @param artist_ids as int
            @param storage_type as StorageType
            @param cancellable as Gio.Cancellable
        """
        names = [App().artists.get_name(artist_id) for artist_id in artist_ids]
        spotify_ids = self.get_similar_artist_ids(names, cancellable)
        track_ids = []
        for spotify_id in spotify_ids:
            spotify_ids = self.get_artist_top_tracks(spotify_id, cancellable)
            # We want some randomizing so keep tracks for later usage
            spotify_id = choice(spotify_ids)
            track_ids += spotify_ids
            payload = self.get_track_payload(spotify_id, cancellable)
            self.save_tracks_payload_to_db([payload],
                                           storage_type,
                                           True,
                                           cancellable)
        shuffle(track_ids)
        for spotify_id in track_ids:
            payload = self.get_track_payload(spotify_id, cancellable)
            self.save_tracks_payload_to_db([payload],
                                           storage_type,
                                           True,
                                           cancellable)
        emit_signal(self, "finished")

    def get_similar_artist_ids(self, artist_names, cancellable):
        """
            Get similar artists
            @param artist_names as [str]
            @param cancellable as Gio.Cancellable
            @return [str] as [spotify ids]
        """
        result = []
        for artist_name in artist_names:
            if cancellable.is_cancelled():
                return []
            spotify_id = self.get_artist_id(artist_name, cancellable)
            if spotify_id is None:
                continue
            if cancellable.is_cancelled():
                return []
            result += self.__get_similar_artists_from_spotify_id(spotify_id,
                                                                 cancellable)
        return [spotify_id for (spotify_id, name, uri) in result]

    def get_similar_artists(self, artist_names, cancellable):
        """
            Get similar artists
            @param artist_names as [str]
            @param cancellable as Gio.Cancellable
            @return [(str, str)] as [(artist_name, cover_uri)]
        """
        result = []
        for artist_name in artist_names:
            if cancellable.is_cancelled():
                return []
            spotify_id = self.get_artist_id(artist_name, cancellable)
            if spotify_id is None:
                continue
            if cancellable.is_cancelled():
                return []
            result += self.__get_similar_artists_from_spotify_id(spotify_id,
                                                                 cancellable)
        result = [(name, uri) for (spotify_id, name, uri) in result]
        if result:
            Logger.info("Found similar artists with SpotifySimilars")
        return result

#######################
# PRIVATE             #
#######################
    def __get_similar_artists_from_spotify_id(self, spotify_id, cancellable):
        """
           Get similar artists from spotify id
           @param spotify_id as str
           @param cancellable as Gio.Cancellable
           @return [(str, str, str)] : list of (spotify_id, artist, cover_uri)
        """
        artists = []
        try:
            while App().token_helper.wait_for_token("SPOTIFY", cancellable):
                if cancellable.is_cancelled():
                    raise Exception("cancelled")
                sleep(1)
            token = "Bearer %s" % App().token_helper.spotify
            helper = TaskHelper()
            helper.add_header("Authorization", token)
            uri = "https://api.spotify.com/v1/artists/%s/related-artists" %\
                spotify_id
            (status, data) = helper.load_uri_content_sync(uri, cancellable)
            if cancellable.is_cancelled():
                raise Exception("cancelled")
            if status:
                decode = json.loads(data.decode("utf-8"))
                for item in decode["artists"]:
                    try:
                        image_uri = item["images"][1]["url"]
                    except:
                        image_uri = None
                    artists.append((item["id"],
                                    item["name"],
                                    image_uri))
        except:
            Logger.error(
                "SpotifySimilars::__get_similar_artists_from_spotify_id(): %s",
                spotify_id)
        return artists
