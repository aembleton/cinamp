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

from lollypop.define import App, SelectionListMask, Type, ScanUpdate


class ScannerContainer:
    """
        Scanner management for main view
    """

    def __init__(self):
        """
            Init container
        """
        App().scanner.connect("genre-updated", self.__on_genre_updated)
        App().scanner.connect("artist-updated", self.__on_artist_updated)

############
# PRIVATE  #
############
    def __on_genre_updated(self, scanner, genre_id, scan_update):
        """
            Add genre to genre list
            @param scanner as CollectionScanner
            @param genre_id as int
            @param scan_update as ScanUpdate
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            if scan_update == ScanUpdate.ADDED:
                genre_name = App().genres.get_name(genre_id)
                self.left_list.add_value((genre_id, genre_name, genre_name))
            elif not App().artists.get_ids([genre_id]):
                self.left_list.remove_value(genre_id)

    def __on_artist_updated(self, scanner, artist_id, scan_update):
        """
            Add/remove artist to/from list
            @param scanner as CollectionScanner
            @param artist_id as int
            @param scan_update as ScanUpdate
        """
        if Type.GENRES_LIST in self.sidebar.selected_ids:
            selection_list = self.right_list
            genre_ids = self.left_list.selected_ids
        elif Type.ARTISTS_LIST in self.sidebar.selected_ids and\
                self.left_list.mask & SelectionListMask.ARTISTS:
            selection_list = self.left_list
            genre_ids = []
        else:
            return
        artist_ids = App().artists.get_ids(genre_ids)
        # We only test add, remove and absent is safe
        if artist_id not in artist_ids and scan_update == ScanUpdate.ADDED:
            return
        artist_name = App().artists.get_name(artist_id)
        sortname = App().artists.get_sortname(artist_id)
        genre_ids = []
        if scan_update == ScanUpdate.ADDED:
            selection_list.add_value((artist_id, artist_name, sortname))
        elif not App().albums.get_ids([artist_id], genre_ids):
            selection_list.remove_value(artist_id)
