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

from gi.repository import Gtk, GLib

from gettext import gettext as _

from lollypop.utils import tracks_to_albums
from lollypop.objects_track import Track
from lollypop.view_albums_list import AlbumsListView
from lollypop.define import App, ViewType, MARGIN_SMALL, Size
from lollypop.helper_signals import SignalsHelper, signals


class CurrentAlbumsView(AlbumsListView, SignalsHelper):
    """
        Popover showing Albums View
    """

    @signals
    def __init__(self, view_type):
        """
            Init view
            @param view_type as ViewType
        """
        AlbumsListView.__init__(self, [], [], view_type | ViewType.PLAYBACK)
        self.__width = Size.MEDIUM
        self.set_property("halign", Gtk.Align.CENTER)
        if view_type & ViewType.DND:
            self.dnd_helper.connect("dnd-finished", self.__on_dnd_finished)
        self.__clear_button = Gtk.Button.new_from_icon_name(
            "edit-clear-all-symbolic",
            Gtk.IconSize.MENU)
        self.__clear_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__clear_button.set_tooltip_text(_("Clear albums"))
        self.__clear_button.set_sensitive(App().player.albums)
        self.__clear_button.connect("clicked", self.__on_clear_clicked)
        self.__clear_button.set_margin_end(MARGIN_SMALL)
        self.__save_button = Gtk.Button.new_from_icon_name(
            "document-new-symbolic",
            Gtk.IconSize.MENU)
        self.__save_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__save_button.set_tooltip_text(_("Create a new playlist"))
        self.__save_button.set_sensitive(App().player.albums)
        self.__save_button.connect("clicked", self.__on_save_clicked)
        self.__jump_button = Gtk.Button.new_from_icon_name(
            "go-jump-symbolic",
            Gtk.IconSize.MENU)
        self.__jump_button.set_relief(Gtk.ReliefStyle.NONE)
        self.__jump_button.connect("clicked", self.__on_jump_clicked)
        self.__jump_button.set_tooltip_text(_("Go to current track"))
        self.__jump_button.set_sensitive(App().player.albums)
        label = Gtk.Label.new("<b>" + _("Playing albums") + "</b>")
        label.set_use_markup(True)
        label.set_hexpand(True)
        label.set_margin_start(2)
        label.get_style_context().add_class("dim-label")
        label.set_property("halign", Gtk.Align.START)
        self.__header = Gtk.Grid()
        self.__header.set_column_spacing(MARGIN_SMALL)
        self.__header.set_margin_top(MARGIN_SMALL)
        self.__header.add(label)
        self.__header.set_property("valign", Gtk.Align.CENTER)
        self.__header.add(self.__jump_button)
        self.__header.add(self.__save_button)
        self.__header.add(self.__clear_button)
        self.__header.show_all()
        self.set_row_spacing(2)
        self.insert_row(0)
        self.attach(self.__header, 0, 0, 1, 1)
        return [
            (App().player, "queue-changed", "_on_queue_changed"),
            (App().player, "playback-changed", "_on_playback_changed")
        ]

    def populate(self):
        """
            Populate view
        """
        self._remove_placeholder()
        if App().player.queue:
            tracks = [Track(track_id) for track_id in App().player.queue]
            albums = tracks_to_albums(tracks)
        else:
            albums = App().player.albums
        AlbumsListView.populate(self, albums)

    def do_get_preferred_width(self):
        return (self.__width, self.__width)

    @property
    def args(self):
        return None

#######################
# PROTECTED           #
#######################
    def _on_queue_changed(self, *ignore):
        """
            Clean view and reload if empty
        """
        queue = App().player.queue
        if queue:
            for row in self.children:
                if row.revealed:
                    for subrow in row.children:
                        if subrow.track.id not in queue:
                            subrow.destroy()
                            break
                count = len(row.album.tracks)
                for track in row.album.tracks:
                    if track.id not in queue:
                        row.album.remove_track(track)
                        if count == 1:
                            row.destroy()
                        break
        else:
            self.stop()
            self.clear()
            self.populate()

    def _on_playback_changed(self, *ignore):
        """
            Clear and populate view again
        """
        self.stop()
        self.clear()
        self.__clear_button.set_sensitive(True)
        self.__jump_button.set_sensitive(True)
        self.__save_button.set_sensitive(True)
        self.populate()

#######################
# PRIVATE             #
#######################
    def __albums_to_playlist(self):
        """
            Create a new playlist based on search
        """
        tracks = []
        for child in self.children:
            tracks += child.album.tracks
        if tracks:
            import datetime
            now = datetime.datetime.now()
            date_string = now.strftime("%Y-%m-%d-%H:%M:%S")
            playlist_id = App().playlists.add(date_string)
            App().playlists.add_tracks(playlist_id, tracks)

    def __on_jump_clicked(self, button):
        """
            Scroll to album
            @param button as Gtk.Button
        """
        self.jump_to_current()

    def __on_save_clicked(self, button):
        """
            Save to playlist
            @param button as Gtk.Button
        """
        button.set_sensitive(False)
        App().task_helper.run(self.__albums_to_playlist)

    def __on_clear_clicked(self, button):
        """
            Clear albums
            @param button as Gtk.Button
        """
        GLib.idle_add(self.clear, True)
        self.__clear_button.set_sensitive(False)
        self.__jump_button.set_sensitive(False)
        self.__save_button.set_sensitive(False)
        App().player.emit("status-changed")
        popover = self.get_ancestor(Gtk.Popover)
        if popover is not None:
            popover.popdown()

    def __on_dnd_finished(self, dnd_helper):
        """
            Save playlist if needed
            @param dnd_helper as DNDHelper
        """
        albums = []
        for child in self.children:
            albums.append(child.album)
        App().player.set_albums(albums)
        App().player.update_next_prev()
