# Copyright (c) 2014-2018 Cedric Bellegarde <cedric.bellegarde@adishatz.org>
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

from lollypop.helper_art import ArtHelperEffect
from lollypop.controller_information import InformationController
from lollypop.controller_progress import ProgressController
from lollypop.controller_playback import PlaybackController
from lollypop.define import App


class MiniPlayer(Gtk.Bin, InformationController,
                 ProgressController, PlaybackController):
    """
        Toolbar end
    """

    def __init__(self, width):
        """
            Init toolbar
            @param width as int
        """
        self.__width = width
        self.__height = 0
        Gtk.Bin.__init__(self)
        InformationController.__init__(self, False, ArtHelperEffect.BLUR)
        ProgressController.__init__(self)
        PlaybackController.__init__(self)
        builder = Gtk.Builder()
        builder.add_from_resource("/org/gnome/Lollypop/MiniPlayer.ui")
        builder.connect_signals(self)

        self.__grid = builder.get_object("grid")
        self.__revealer = builder.get_object("revealer")

        self._progress = builder.get_object("progress_scale")
        self._progress.set_sensitive(False)
        self._progress.set_hexpand(True)
        self._timelabel = builder.get_object("playback")
        self._total_time_label = builder.get_object("duration")

        self._prev_button = builder.get_object("previous_button")
        self._play_button = builder.get_object("play_button")
        self._next_button = builder.get_object("next_button")
        self.__back_button = builder.get_object("back_button")
        self._play_image = builder.get_object("play_image")
        self._pause_image = builder.get_object("pause_image")

        self.__grid = builder.get_object("grid")
        self._title_label = builder.get_object("title")
        self._artist_label = builder.get_object("artist")
        self._artwork = builder.get_object("cover")
        self.__signal_id1 = App().player.connect("current-changed",
                                                 self.__on_current_changed)
        self.__signal_id2 = App().player.connect("status-changed",
                                                 self.__on_status_changed)
        self.__signal_id3 = App().player.connect("lock-changed",
                                                 self.__on_lock_changed)
        self.__on_current_changed(App().player)
        if App().player.current_track.id is not None:
            self.update_position()
            ProgressController.on_status_changed(self, App().player)
        self.add(builder.get_object("widget"))

    def update_labels(self, *ignore):
        """
            No labels here
        """
        pass

    def update_cover(self, width):
        """
            Update cover for width
            @param width as int
        """
        self.__width = width
        InformationController.on_current_changed(self, width, None)

    def do_get_preferred_width(self):
        """
            Force preferred width
        """
        (min, nat) = Gtk.Bin.do_get_preferred_width(self)
        # Allow resizing
        return (0, 0)

    def do_get_preferred_height(self):
        """
            Force preferred height
        """
        return self.__grid.get_preferred_height()

    def do_destroy(self):
        """
            Remove signal
        """
        ProgressController.do_destroy(self)
        App().player.disconnect(self.__signal_id1)
        App().player.disconnect(self.__signal_id2)
        App().player.disconnect(self.__signal_id3)

#######################
# PROTECTED           #
#######################
    def _on_reveal_button_clicked(self, button):
        """
            Set revealer on/off
            @param button as Gtk.Button
        """
        if self.__revealer.get_reveal_child():
            button.get_image().set_from_icon_name("pan-up-symbolic",
                                                  Gtk.IconSize.BUTTON)
            self.__revealer.set_reveal_child(False)
        else:
            button.get_image().set_from_icon_name("pan-down-symbolic",
                                                  Gtk.IconSize.BUTTON)
            self.__revealer.set_reveal_child(True)

#######################
# PRIVATE             #
#######################
    def __on_current_changed(self, player):
        """
            Update controllers
            @param player as Player
        """
        if App().player.current_track.id is not None:
            self.show()
        InformationController.on_current_changed(self, self.__width, None)
        ProgressController.on_current_changed(self, player)
        PlaybackController.on_current_changed(self, player)

    def __on_status_changed(self, player):
        """
            Update controllers
            @param player as Player
        """
        ProgressController.on_status_changed(self, player)
        PlaybackController.on_status_changed(self, player)

    def __on_lock_changed(self, player):
        """
            Lock toolbar
            @param player as Player
        """
        self._prev_button.set_sensitive(not player.is_locked)
        self._next_button.set_sensitive(not player.is_locked)
