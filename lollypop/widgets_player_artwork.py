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

from gi.repository import Gtk

from lollypop.define import App, ArtBehaviour
from lollypop.objects_album import Album
from lollypop.objects_radio import Radio
from lollypop.helper_signals import SignalsHelper, signals


class ArtworkPlayerWidget(Gtk.Image, SignalsHelper):
    """
        Gtk.Image auto updated with current player state
    """

    @signals
    def __init__(self, behaviour=ArtBehaviour.CACHE):
        """
            Init artwork
            @param effect as effect=ArtBehaviour
        """
        Gtk.Image.__init__(self)
        self.__behaviour = behaviour
        self.__width = self.__height = 1
        self.__previous_artwork_id = None
        self.__per_track_cover = App().settings.get_value(
            "allow-per-track-cover")
        return [
            (App().player, "current-changed", "_on_current_changed"),
            (App().art, "album-artwork-changed", "_on_album_artwork_changed"),
            (App().art, "radio-artwork-changed", "_on_radio_artwork_changed")
        ]

    def set_art_size(self, width, height):
        """
            Set artwork width/height
            @param width as int
            @param heigth as int
        """
        self.__width = width
        self.__height = height

    def update(self):
        """
            Update artwork
        """
        same_artwork = self.__previous_artwork_id ==\
            App().player.current_track.album.id and not self.__per_track_cover
        if same_artwork:
            return
        self.__previous_artwork_id = App().player.current_track.album.id
        self.set_artwork(self.__width, self.__height,
                         self.__on_artwork, self.__behaviour)

    def set_behaviour(self, behaviour):
        """
            Set artwork behaviour
            @param behaviour as ArtBehaviour
        """
        self.__behaviour = behaviour
        self.__previous_artwork_id = None

    def set_artwork(self, width, height, callback, behaviour):
        """
            Set artwork
            @param width as int
            @param height as int
            @param callback as function
        """
        scale_factor = self.get_scale_factor()
        if isinstance(App().player.current_track, Radio):
            App().art_helper.set_radio_artwork(
                App().player.current_track.name,
                width,
                height,
                scale_factor,
                behaviour,
                callback)
        elif App().player.current_track.id is not None:
            if self.__per_track_cover:
                behaviour |= ArtBehaviour.NO_CACHE
                album = Album(App().player.current_track.album.id)
                App().art.clean_album_cache(album,
                                            width * scale_factor,
                                            height * scale_factor)
                album.set_tracks([App().player.current_track])
            else:
                album = App().player.current_track.album
            App().art_helper.set_album_artwork(
                album,
                width,
                height,
                scale_factor,
                behaviour,
                callback)

#######################
# PROTECTED           #
#######################
    def _on_current_changed(self, player):
        """
            Update artwork and labels
            @param player as Player
        """
        self.update()

    def _on_album_artwork_changed(self, art, album_id):
        """
            Update cover for album_id
            @param art as Art
            @param album_id as int
        """
        if App().player.current_track.album.id == album_id:
            self.set_artwork(self.__width, self.__height,
                             self.__on_artwork, self.__behaviour)

    def _on_radio_artwork_changed(self, art, name):
        """
            Update logo for name
            @param art as Art
            @param name as str
        """
        if App().player.current_track.album_artist == name:
            self.set_artwork(self.__width, self.__height,
                             self.__on_artwork, self.__behaviour)

#######################
# PRIVATE             #
#######################
    def __on_artwork(self, surface):
        """
            Set artwork
            @param surface as str
        """
        if surface is None:
            if isinstance(App().player.current_track, Radio):
                icon_name = "audio-input-microphone-symbolic"
            else:
                icon_name = "folder-music-symbolic"
            self.set_from_icon_name(icon_name, Gtk.IconSize.BUTTON)
            self.set_size_request(self._art_size, self._art_size)
        else:
            self.set_from_surface(surface)