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

from gi.repository import GLib, Gtk, Gio, Pango

from gettext import gettext as _

from lollypop.define import App, Type, MARGIN, ViewType, StorageType
from lollypop.objects_album import Album
from lollypop.utils import get_network_available, get_default_storage_type
from lollypop.helper_signals import signals
from lollypop.helper_horizontal_scrolling import HorizontalScrollingHelper
from lollypop.view_albums_box import AlbumsBoxView


class AlbumsLineView(AlbumsBoxView, HorizontalScrollingHelper):
    """
        Albums on a line
    """

    ITEMS = 20

    def __init__(self, storage_type, view_type):
        """
            Init view
            @param view_type as ViewType
            @param storage_type as StorageType
        """
        AlbumsBoxView.__init__(self, [], [], storage_type, view_type)
        self.set_property("valign", Gtk.Align.START)
        self._label = Gtk.Label.new()
        self._label.set_ellipsize(Pango.EllipsizeMode.END)
        self._label.set_hexpand(True)
        self._label.set_property("halign", Gtk.Align.START)
        self._label.get_style_context().add_class("dim-label")
        self.__update_label(App().window.is_adaptive)
        self._backward_button = Gtk.Button.new_from_icon_name(
                                                        "go-previous-symbolic",
                                                        Gtk.IconSize.BUTTON)
        self._forward_button = Gtk.Button.new_from_icon_name(
                                                       "go-next-symbolic",
                                                       Gtk.IconSize.BUTTON)
        self._backward_button.get_style_context().add_class("menu-button")
        self._forward_button.get_style_context().add_class("menu-button")
        header = Gtk.Grid()
        header.set_column_spacing(10)
        header.add(self._label)
        header.add(self._backward_button)
        header.add(self._forward_button)
        header.set_margin_end(MARGIN)
        header.show_all()
        HorizontalScrollingHelper.__init__(self)
        self.add(header)
        self.add_widget(self._box)

    def populate(self, albums):
        """
            Configure widget based on albums
            @param items as [Album]
        """
        if albums:
            self.show()
            self._box.set_min_children_per_line(len(albums))
            AlbumsBoxView.populate(self, albums)

    @property
    def args(self):
        return None

#######################
# PROTECTED           #
#######################
    def _on_album_updated(self, scanner, album_id, scan_update):
        pass

    def _on_adaptive_changed(self, window, status):
        """
            Update label
            @param window as Window
            @param status as bool
        """
        AlbumsBoxView._on_adaptive_changed(self, window, status)
        self.__update_label(status)

#######################
# PRIVATE             #
#######################
    def __update_label(self, is_adaptive):
        """
            Update label style based on current adaptive state
            @param is_adaptive as bool
        """
        style_context = self._label.get_style_context()
        if is_adaptive:
            style_context.remove_class("text-x-large")
        else:
            style_context.add_class("text-x-large")


class AlbumsArtistLineView(AlbumsLineView):
    """
        Artist album line
    """

    def __init__(self,  album, artist_id, storage_type, view_type):
        """
            Init view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsLineView.__init__(self, storage_type, view_type)
        self.__album = album
        self.__artist_id = artist_id

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            AlbumsLineView.populate(self, items)

        def load():
            if self.__artist_id == Type.COMPILATIONS:
                album_ids = App().albums.get_compilation_ids(
                    self.__album.genre_ids, self.storage_type)
            else:
                album_ids = App().albums.get_ids(
                    [self.__artist_id], [], self.storage_type)
            if self.__album.id in album_ids:
                album_ids.remove(self.__album.id)
            return [Album(album_id) for album_id in album_ids]

        if self.__artist_id == Type.COMPILATIONS:
            self._label.set_text(_("Others compilations"))
        else:
            self._label.set_text(App().artists.get_name(self.__artist_id))
        App().task_helper.run(load, callback=(on_load,))


class AlbumsPopularsLineView(AlbumsLineView):
    """
        Populars albums line
    """

    def __init__(self, storage_type, view_type):
        """
            Init view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsLineView.__init__(self, storage_type, view_type)

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            AlbumsLineView.populate(self, items)

        def load():
            storage_type = get_default_storage_type()
            album_ids = App().albums.get_populars_at_the_moment(storage_type,
                                                                self.ITEMS)
            return [Album(album_id) for album_id in album_ids]

        self._label.set_text(_("Popular albums at the moment"))
        App().task_helper.run(load, callback=(on_load,))


class AlbumsRandomGenresLineView(AlbumsLineView):
    """
        Populars albums line
    """

    def __init__(self, storage_type, view_type):
        """
            Init view
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsLineView.__init__(self, storage_type, view_type)

    def populate(self):
        """
            Populate view
        """
        def on_load(items):
            AlbumsLineView.populate(self, items)

        def load():
            (genre_id, genre) = App().genres.get_random()
            GLib.idle_add(self._label.set_text, genre)
            storage_type = get_default_storage_type()
            album_ids = App().albums.get_randoms(storage_type,
                                                 genre_id,
                                                 self.ITEMS)
            return [Album(album_id) for album_id in album_ids]

        App().task_helper.run(load, callback=(on_load,))


class AlbumsSearchLineView(AlbumsLineView):
    """
        Search album line
    """
    def __init__(self, storage_type):
        """
            Init view
            @param storage_type as StorageType
        """
        AlbumsLineView.__init__(self, storage_type, ViewType.SEARCH |
                                ViewType.SCROLLED)
        self.__album_ids = []
        self._label.set_text(_("Albums"))

    def add_album(self, album):
        """
            Insert item
            @param album as Album
        """
        if album.id in self.__album_ids:
            return
        self.__album_ids.append(album.id)
        AlbumsLineView.insert_album(self, album, -1)
        self._box.set_min_children_per_line(len(self._box.get_children()))

    def clear(self):
        """
            Clear and hide the view
        """
        self.__album_ids = []
        AlbumsLineView.clear(self)
        GLib.idle_add(self.hide)


class AlbumsSpotifyLineView(AlbumsLineView):
    """
        Spotify album line
    """

    @signals
    def __init__(self, text, storage_type, view_type):
        """
            Init view
            @param text as str
            @param storage_type as StorageType
            @param view_type as ViewType
        """
        AlbumsLineView.__init__(self, storage_type, view_type)
        self._label.set_text(text)
        self.__cancellable = Gio.Cancellable()
        self.__storage_type = StorageType.NONE
        return [
                (App().spotify, "match-album", "_on_album_match"),
                (App().settings, "changed::network-access",
                 "_on_network_access_changed"),
                (App().settings, "changed::network-access-acl",
                 "_on_network_access_changed")
        ]

    def populate(self, storage_type):
        """
            Populate view
            @param storage_type as StorageType
        """
        def on_load(items):
            AlbumsLineView.populate(self, items)

        def load():
            album_ids = App().albums.get_for_storage_type(storage_type, 20)
            return [Album(album_id) for album_id in album_ids]

        App().task_helper.run(load, callback=(on_load,))
        self.__storage_type |= storage_type

#######################
# PROTECTED           #
#######################
    def _on_unmap(self, widget):
        """
            Cancel search
            @param widget as Gtk.Widget
        """
        self.__cancellable.cancel()
        self.__cancellable = Gio.Cancellable()

    def _on_album_match(self, spotify_helper, album_id, storage_type):
        """
            Handles changes in collection
            @param scanner as CollectionScanner
            @param album_id as int
            @param storage_type as StorageType
        """
        count = len(self.children)
        if count == self.ITEMS:
            return
        if self.__storage_type & storage_type:
            self.insert_album(Album(album_id), -1)
            self._box.set_min_children_per_line(count + 1)
            self.show()

    def _on_network_access_changed(self, *ignore):
        """
            Destroy if not allowed anymore
        """
        if not get_network_available("SPOTIFY") or\
                not get_network_available("YOUTUBE"):
            self.destroy()

#####################
# PRIVATE           #
#####################
