# Copyright (c) 2014-2019 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from gi.repository import Gst, GstPbutils, GLib, Gio

from re import match
from gettext import gettext as _

from lollypop.define import App
from lollypop.logger import Logger
from lollypop.utils import format_artist_name


class Discoverer:
    """
        Discover tags
    """

    def __init__(self):
        """
            Init tag reader
        """
        self.init_discoverer()

    def init_discoverer(self):
        """
            Init discover
        """
        GstPbutils.pb_utils_init()
        self._discoverer = GstPbutils.Discoverer.new(10 * Gst.SECOND)

    def get_info(self, uri):
        """
            Return information for file at uri
            @param uri as str
            @Exception GLib.Error
            @return GstPbutils.DiscovererInfo
        """
        info = self._discoverer.discover_uri(uri)
        return info


class TagReader(Discoverer):
    """
        Scanner tag reader
    """

    def __init__(self):
        """
            Init tag reader
        """
        Discoverer.__init__(self)

    def get_title(self, tags, filepath):
        """
            Return title for tags
            @param tags as Gst.TagList
            @param filepath as string
            @return title as string
        """
        if tags is None:
            return GLib.path_get_basename(filepath)
        (exists, title) = tags.get_string_index("title", 0)
        # We need to check tag is not just spaces
        if not exists or not title.strip(" "):
            title = GLib.path_get_basename(filepath)
        return title

    def get_artists(self, tags):
        """
            Return artists for tags
            @param tags as Gst.TagList
            @return string like "artist1;artist2;..."
        """
        if tags is None:
            return _("Unknown")
        artists = []
        for i in range(tags.get_tag_size("artist")):
            (exists, read) = tags.get_string_index("artist", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                artists.append(read)
        return "; ".join(artists)

    def get_composers(self, tags):
        """
            Return composers for tags
            @param tags as Gst.TagList
            @return string like "composer1;composer2;..."
        """
        if tags is None:
            return _("Unknown")
        composers = []
        for i in range(tags.get_tag_size("composer")):
            (exists, read) = tags.get_string_index("composer", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                composers.append(read)
        return "; ".join(composers)

    def get_mb_id(self, tags, name):
        """
            Get MusicBrainz ID
            @param tags as Gst.TagList
            @param name as str
            @return str
        """
        if tags is None or not name:
            return ""
        (exists, mbid) = tags.get_string_index("musicbrainz-" + name, 0)
        return mbid or ""

    def get_mb_album_id(self, tags):
        """
            Get album id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'albumid')

    def get_mb_track_id(self, tags):
        """
            Get recording id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'trackid')

    def get_mb_artist_id(self, tags):
        """
            Get artist id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'artistid')

    def get_mb_album_artist_id(self, tags):
        """
            Get album artist id (musicbrainz)
            @param tags as Gst.TagList
            @return str
        """
        return self.get_mb_id(tags, 'albumartistid')

    def get_version(self, tags):
        """
            Get recording version
            @param tags as Gst.TagList
            @return str
        """
        if tags is None:
            return ""
        (exists, version) = tags.get_string_index("version", 0)
        return version or ""

    def get_performers(self, tags):
        """
            Return performers for tags
            @param tags as Gst.TagList
            @return string like "performer1;performer2;..."
        """
        if tags is None:
            return _("Unknown")
        performers = []
        for i in range(tags.get_tag_size("performer")):
            (exists, read) = tags.get_string_index("performer", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                performers.append(read)
        return "; ".join(performers)

    def get_artist_sortnames(self, tags):
        """
            Return artist sort names
            @param tags as Gst.TagList
            @return artist sort names as "str;str"
        """
        if tags is None:
            return ""
        sortnames = []
        for i in range(tags.get_tag_size("artist-sortname")):
            (exists, read) = tags.get_string_index("artist-sortname", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                sortnames.append(read)
        return "; ".join(sortnames)

    def get_album_artist_sortnames(self, tags):
        """
            Return album artist sort names
            @param tags as Gst.TagList
            @return artist sort names as "str;str"
        """
        if tags is None:
            return ""
        sortnames = []
        for i in range(tags.get_tag_size("album-artist-sortname")):
            (exists, read) = tags.get_string_index("album-artist-sortname", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                sortnames.append(read)
        return "; ".join(sortnames)

    def get_remixers(self, tags):
        """
            Get remixers tag
            @param tags as Gst.TagList
            @return artist sort names as "str,str"
        """
        if tags is None:
            return _("Unknown")
        remixers = []
        for i in range(tags.get_tag_size("interpreted-by")):
            (exists, read) = tags.get_string_index("interpreted-by", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                remixers.append(read)
        if not remixers:
            for i in range(tags.get_tag_size("extended-comment")):
                (exists, read) = tags.get_string_index("extended-comment", i)
                if exists and read.startswith("REMIXER="):
                    remixer = read[8:]
                    remixers.append(remixer)
        return "; ".join(remixers)

    def get_album_artists(self, tags):
        """
            Return album artists for tags
            @param tags as Gst.TagList
            @return album artist as string or None
        """
        if tags is None:
            return _("Unknown")
        artists = []
        for i in range(tags.get_tag_size("album-artist")):
            (exists, read) = tags.get_string_index("album-artist", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                artists.append(read)
        return "; ".join(artists)

    def get_album_name(self, tags):
        """
            Return album for tags
            @param tags as Gst.TagList
            @return album name as string
        """
        if tags is None:
            return _("Unknown")
        (exists, album_name) = tags.get_string_index("album", 0)
        # We need to check tag is not just spaces
        if not exists or not album_name.strip(" "):
            album_name = _("Unknown")
        return album_name

    def get_genres(self, tags):
        """
            Return genres for tags
            @param tags as Gst.TagList
            @return string like "genre1;genre2;..."
        """
        if tags is None:
            return _("Unknown")
        genres = []
        for i in range(tags.get_tag_size("genre")):
            (exists, read) = tags.get_string_index("genre", i)
            # We need to check tag is not just spaces
            if exists and read.strip(" "):
                genres.append(read)
        if not genres:
            return _("Unknown")
        return "; ".join(genres)

    def get_discname(self, tags):
        """
            Return disc name
            @param tags as Gst.TagList
            @return disc name as str
        """
        if tags is None:
            return 0
        discname = ""
        for i in range(tags.get_tag_size("extended-comment")):
            (exists, read) = tags.get_string_index("extended-comment", i)
            if exists and read.startswith("PART"):
                discname = "=".join(read.split("=")[1:])
                break
            if exists and read.startswith("DISCSUBTITLE"):
                discname = "=".join(read.split("=")[1:])
                break
        return discname

    def get_discnumber(self, tags):
        """
            Return disc number for tags
            @param tags as Gst.TagList
            @return disc number as int
        """
        if tags is None:
            return 0
        (exists, discnumber) = tags.get_uint_index("album-disc-number", 0)
        if not exists:
            discnumber = 0
        return discnumber

    def get_tracknumber(self, tags, filename):
        """
            Return track number for tags
            @param tags as Gst.TagList
            @param filename as str
            @return track number as int
        """
        if tags is not None:
            (exists, tracknumber) = tags.get_uint_index("track-number", 0)
        else:
            (exists, tracknumber) = (False, 0)
        if not exists:
            # Guess from filename
            m = match("^([0-9]*)[ ]*-", filename)
            if m:
                try:
                    tracknumber = int(m.group(1))
                except:
                    tracknumber = 0
            else:
                tracknumber = 0
        return min(abs(tracknumber), GLib.MAXINT32)

    def get_year(self, tags):
        """
            Return track year for tags
            @param tags as Gst.TagList
            @return year and timestamp (int, int)
        """
        try:
            (exists, date) = tags.get_date_index("date", 0)
            dt = year = timestamp = None
            if exists:
                year = date.get_year()
                d = Gst.DateTime.new_local_time(year, 1, 1, 0, 0, 0)
                dt = d.to_g_date_time()
                timestamp = dt.to_unix()
            else:
                (exists, date) = tags.get_date_time_index("datetime", 0)
                if exists:
                    dt = date.to_g_date_time()
                    if dt is None:
                        year = date.get_year()
                        d = Gst.DateTime.new_local_time(year, 1, 1, 0, 0, 0)
                        dt = d.to_g_date_time()
                    timestamp = dt.to_unix()
            return (year, timestamp)
        except Exception as e:
            error = "" if tags is None else tags.to_string()
            Logger.error("TagReader::get_year(): %s, %s", e, error)
        return (None, None)

    def get_original_year(self, tags):
        """
            Return original release year
            @param tags as Gst.TagList
            @return year and timestamp (int, int)
        """
        def get_id3():
            try:
                size = tags.get_tag_size("private-id3v2-frame")
                for i in range(0, size):
                    (exists, sample) = tags.get_sample_index(
                        "private-id3v2-frame",
                        i)
                    if not exists:
                        continue
                    (exists, m) = sample.get_buffer().map(Gst.MapFlags.READ)
                    if not exists:
                        continue
                    string = m.data.decode("utf-8")
                    if string.startswith("TDOR"):
                        split = string.split("\x00")
                        date = split[-1]
                        datetime = GLib.DateTime.new_from_iso8601(date, None)
                        return (datetime.year(), datetime.to_unix())
            except:
                pass
            return (None, None)

        def get_ogg():
            try:
                size = tags.get_tag_size("extended-comment")
                for i in range(0, size):
                    (exists, sample) = tags.get_string_index(
                        "extended-comment",
                        i)
                    if not exists or not sample.startswith("ORIGINALDATE="):
                        continue
                    date = sample[13:]
                    datetime = GLib.DateTime.new_from_iso8601(date, None)
                    return (datetime.year(), datetime.to_unix())
            except:
                pass
            return None

        if tags is None:
            return None
        values = get_id3()
        if values is None:
            values = get_ogg()
        return values

    def get_bpm(self, tags):
        """
            Get BPM from tags
            @param tags as Gst.TagList
            @return int/None
        """
        try:
            if tags is not None:
                (exists, bpm) = tags.get_double_index("beats-per-minute", 0)
                if exists:
                    return bpm
        except:
            pass
        return None

    def get_popm(self, tags):
        """
            Get popularity tag
            @param tags as Gst.TagList
            @return value as Lollypop rating
        """
        if tags is None:
            return 0
        size = tags.get_tag_size("private-id3v2-frame")
        for i in range(0, size):
            (exists, sample) = tags.get_sample_index("private-id3v2-frame", i)
            if not exists:
                continue
            (exists, m) = sample.get_buffer().map(Gst.MapFlags.READ)
            if not exists:
                continue
            if m.data[0:4] == b"POPM":
                # Get tag
                popm = m.data[11]
                if popm == 0:
                    value = 0
                elif popm == 1:
                    value = 1
                elif popm == 64:
                    value = 2
                elif popm == 128:
                    value = 3
                elif popm == 196:
                    value = 4
                else:
                    value = 5
                return value
        return 0

    def get_lyrics(self, tags):
        """
            Return lyrics for tags
            All this code sucks
            @parma tags as Gst.TagList
            @return lyrics as str
        """
        def decode_lyrics(bytes):
            from lollypop.utils import decodeUnicode, splitUnicode
            try:
                prefix = bytes[0:4]
                if prefix in [b"USLT"]:
                    frame = bytes[10:]
                    encoding = frame[0:1]
                    (d, t) = splitUnicode(frame[4:], encoding)
                    return decodeUnicode(t, encoding)
            except Exception as e:
                Logger.warning("TagReader::get_lyrics(): %s", e)
            return None

        def get_mp4():
            try:
                (exists, sample) = tags.get_string_index("lyrics", 0)
                if exists:
                    return sample
            except Exception as e:
                Logger.error("TagReader::get_mp4(): %s" % e)
            return ""

        def get_id3():
            try:
                size = tags.get_tag_size("private-id3v2-frame")
                for i in range(0, size):
                    (exists, sample) = tags.get_sample_index(
                        "private-id3v2-frame",
                        i)
                    if not exists:
                        continue
                    (exists, m) = sample.get_buffer().map(Gst.MapFlags.READ)
                    if not exists:
                        continue
                    string = decode_lyrics(m.data)
                    if string is not None:
                        return string
            except Exception as e:
                Logger.error("TagReader::get_id3(): %s" % e)
            return ""

        def get_ogg():
            try:
                size = tags.get_tag_size("extended-comment")
                for i in range(0, size):
                    (exists, sample) = tags.get_string_index(
                        "extended-comment",
                        i)
                    if not exists or not sample.startswith("LYRICS="):
                        continue
                    return sample[7:]
            except Exception as e:
                Logger.error("TagReader::get_ogg(): %s" % e)
            return ""

        if tags is None:
            return ""
        lyrics = get_mp4()
        if not lyrics:
            lyrics = get_id3()
        if not lyrics:
            lyrics = get_ogg()
        return lyrics

    def add_artists(self, artists, sortnames, mb_artist_ids=""):
        """
            Add artists to db
            @param artists as [string]
            @param sortnames as [string]
            @param mb_artist_ids as [string]
            @return [int]
            @commit needed
        """
        artist_ids = []
        artistsplit = artists.split(";")
        sortsplit = sortnames.split(";")
        sortlen = len(sortsplit)
        mbidsplit = mb_artist_ids.split(";")
        mbidlen = len(mbidsplit)
        if len(artistsplit) != mbidlen:
            mbidsplit = []
            mbidlen = 0
        i = 0
        for artist in artistsplit:
            artist = artist.strip()
            if artist != "":
                if i >= mbidlen or mbidsplit[i] == "":
                    mbid = None
                else:
                    mbid = mbidsplit[i].strip()
                # Get artist id, add it if missing
                artist_id = App().artists.get_id(artist, mbid)
                if i >= sortlen or sortsplit[i] == "":
                    sortname = None
                else:
                    sortname = sortsplit[i].strip()
                if artist_id is None:
                    if sortname is None:
                        sortname = format_artist_name(artist)
                    artist_id = App().artists.add(artist, sortname, mbid)
                else:
                    if sortname is not None:
                        App().artists.set_sortname(artist_id, sortname)
                    if mbid is not None:
                        App().artists.set_mb_artist_id(artist_id, mbid)
                i += 1
                artist_ids.append(artist_id)
        return artist_ids

    def add_genres(self, genres):
        """
            Add genres to db
            @param genres as string
            @return genre ids as [int]
            @commit needed
        """
        # Get all genre ids
        genre_ids = []
        for genre in genres.split(";"):
            genre = genre.strip()
            if genre != "":
                # Get genre id, add genre if missing
                genre_id = App().genres.get_id(genre)
                if genre_id is None:
                    genre_id = App().genres.add(genre)
                genre_ids.append(genre_id)
        return genre_ids

    def add_album(self, album_name, mb_album_id, artist_ids,
                  uri, loved, popularity, rate, mtime):
        """
            Add album to db
            @param album_name as str
            @param mb_album_id as str
            @param artist_ids as [int]
            @param uri as str
            @param loved as bool
            @param popularity as int
            @param rate as int
            @param mtime as int
            @return (added as bool, album_id as int)
            @commit needed
        """
        added = False
        f = Gio.File.new_for_uri(uri)
        d = f.get_parent()
        parent_uri = "" if d is None else d.get_uri()
        album_id = App().albums.get_id(album_name, mb_album_id, artist_ids)
        if album_id is None:
            added = True
            album_id = App().albums.add(album_name, mb_album_id, artist_ids,
                                        parent_uri, loved, popularity,
                                        rate, mtime)
        # Now we have our album id, check if path doesn"t change
        if App().albums.get_uri(album_id) != parent_uri:
            App().albums.set_uri(album_id, parent_uri)
        return (added, album_id)
