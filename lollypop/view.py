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

from gi.repository import Gtk, GLib, Pango

from time import time
from gettext import gettext as _
import gc

from lollypop.define import ViewType, Type, App
from lollypop.logger import Logger
from lollypop.adaptive import AdaptiveView


class View(AdaptiveView, Gtk.Grid):
    """
        Generic view
    """

    def __init__(self, view_type=ViewType.DEFAULT):
        """
            Init view
            @param view_type as ViewType
        """
        AdaptiveView.__init__(self)
        Gtk.Grid.__init__(self)
        self._view_type = view_type
        self.__adaptive_signal_id = None
        self.__destroyed = False
        self._sidebar_id = Type.NONE
        self.__scanner_signal_id = App().scanner.connect(
            "album-updated", self._on_album_updated)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_border_width(0)
        self.__new_ids = []
        self._empty_message = _("No items to show")
        self._empty_icon_name = "emblem-music-symbolic"

        if App().window.is_adaptive:
            self._view_type |= self.view_sizing_mask

        if self._view_type & ViewType.SCROLLED:
            self._scrolled = Gtk.ScrolledWindow()
            self._scrolled.get_vadjustment().connect("value-changed",
                                                     self._on_value_changed)
            self._scrolled.show()
            self._viewport = Gtk.Viewport()
            self._scrolled.add(self._viewport)
            self._viewport.show()

        self.connect("destroy", self.__on_destroy)
        self.connect("map", self._on_map)
        self.connect("unmap", self._on_unmap)
        self.__adaptive_signal_id = App().window.connect(
                                                "adaptive-changed",
                                                self._on_adaptive_changed)
        if not view_type & (ViewType.POPOVER | ViewType.SEARCH):
            self.get_style_context().add_class("view")

    def populate(self):
        """
            Populate view with default message
        """
        if self._view_type & ViewType.SCROLLED:
            self._scrolled.hide()
        grid = Gtk.Grid()
        grid.set_margin_start(20)
        grid.set_margin_end(20)
        grid.set_column_spacing(20)
        label = Gtk.Label.new()
        label.set_markup("<b>%s</b>" % GLib.markup_escape_text(
            self._empty_message))
        label_style = label.get_style_context()
        label_style.add_class("text-xx-large")
        label_style.add_class("dim-label")
        label.set_line_wrap_mode(Pango.WrapMode.WORD)
        label.set_line_wrap(True)
        image = Gtk.Image.new_from_icon_name(self._empty_icon_name,
                                             Gtk.IconSize.DIALOG)
        image.get_style_context().add_class("dim-label")
        grid.add(image)
        grid.add(label)
        grid.set_vexpand(True)
        grid.set_hexpand(True)
        grid.set_property("halign", Gtk.Align.CENTER)
        grid.set_property("valign", Gtk.Align.CENTER)
        grid.set_name("lollypop_placeholder")
        grid.show_all()
        self.add(grid)

    def stop(self):
        pass

    def enable_filter(self):
        """
           Filter the view
        """
        if self._filter is not None:
            pass

    @property
    def sidebar_id(self):
        """
            Get sidebar id
            @return int
        """
        return self._sidebar_id

    @property
    def args(self):
        """
            Get default args for __class__, populate() plus sidebar_id and
            scrolled position
            @return ({}, {}, int, int) or None
        """
        return None

    @property
    def destroyed(self):
        """
            True if widget has been destroyed
            @return bool
        """
        return self.__destroyed

    @property
    def view_sizing_mask(self):
        """
            Get mask relative to adaptive mode
            @return ViewType
        """
        return ViewType.SMALL

#######################
# PROTECTED           #
#######################
    def _remove_placeholder(self):
        """
            Remove any placeholder
        """
        if self._scrolled.get_visible():
            return
        for child in self.get_children():
            if child.get_name() == "lollypop_placeholder":
                child.destroy()
                break
        self._scrolled.show()

    def _on_adaptive_changed(self, window, status):
        """
            Handle adaptive mode for views
        """
        if status:
            self._view_type |= self.view_sizing_mask
        else:
            self._view_type &= ~self.view_sizing_mask

    def _on_value_changed(self, adj):
        """
            Handle change on scroll
            @param adj as Gtk.Adjustment
        """
        pass

    def _on_album_updated(self, scanner, album_id, added):
        """
            Handles changes in collection
            @param scanner as CollectionScanner
            @param album_id as int
            @param added as bool
        """
        pass

    def _on_map(self, widget):
        """
            Handles special shortcuts
            @param widget as Gtk.Widget
        """
        selected_ids = App().window.container.sidebar.selected_ids
        if selected_ids:
            self._sidebar_id = selected_ids[0]

    def _on_unmap(self, widget):
        """
            Handles special shortcuts
            @param widget as Gtk.Widget
        """
        pass

#######################
# PRIVATE             #
#######################
    def __on_destroy(self, widget):
        """
            Clean up widget
            @param widget as Gtk.Widget
        """
        if self.__adaptive_signal_id is not None:
            App().window.disconnect(self.__adaptive_signal_id)
            self.__adaptive_signal_id = None
        if self.__scanner_signal_id is not None:
            App().scanner.disconnect(self.__scanner_signal_id)
            self.__scanner_signal_id = None
        self.__destroyed = True
        gc.collect()


class LazyLoadingView(View):
    """
        Lazy loading for view
    """

    def __init__(self, view_type=ViewType.DEFAULT):
        """
            Init lazy loading
            @param view_type as ViewType
        """
        View.__init__(self, view_type)
        self.__is_populated = False
        self._lazy_queue = []
        self.__priority_queue = []
        self.__scroll_timeout_id = None
        self.__scrolled_position = None
        self.__lazy_loading_id = None
        self.__start_time = time()

    def stop(self, clear=False):
        """
            Stop loading
            @param clear as bool
        """
        self.__lazy_loading_id = None
        if clear:
            self._lazy_queue = []
            self.__priority_queue = []
        View.stop(self)

    def lazy_loading(self):
        """
            Load the view in a lazy way
        """
        # He we keep id just to check we are in current load
        if self.__lazy_loading_id is None:
            self.__lazy_loading_id = GLib.idle_add(self.__lazy_loading)

    def set_populated_scrolled_position(self, position):
        """
            Set scrolled position on populated
            @param position as int
        """
        if self._view_type & ViewType.SCROLLED:
            self.__scrolled_position = position

    @property
    def is_populated(self):
        """
            True if populated
            @return bool
        """
        return self.__is_populated

#######################
# PROTECTED           #
#######################
    def _on_map(self, widget):
        """
            Restore backup and load
            @param widget as Gtk.Widget
        """
        View._on_map(self, widget)
        # Wait for viewport allocation to restore scrolled position
        if self.__scrolled_position is not None:
            self._viewport.connect("size-allocate",
                                   self.__on_viewport_size_allocated)
        if self._lazy_queue:
            self.lazy_loading()

    def _on_value_changed(self, adj):
        """
            Update scroll value and check for lazy queue
            @param adj as Gtk.Adjustment
        """
        if not self._lazy_queue:
            return False
        if self.__scroll_timeout_id is not None:
            GLib.source_remove(self.__scroll_timeout_id)
        self.__scroll_timeout_id = GLib.timeout_add(200, self.__lazy_or_not)

    def _on_populated(self, widget, lazy_loading_id):
        """
            Add another album/disc
            @param widget as AlbumWidget/TracksView
            @parma lazy_loading_id as int
        """
        if lazy_loading_id != self.__lazy_loading_id:
            return
        if not widget.is_populated:
            widget.populate()
        else:
            self.__lazy_loading()

#######################
# PRIVATE             #
#######################
    def __lazy_loading(self):
        """
            Load the view in a lazy way
        """
        widget = None
        if self.__priority_queue:
            widget = self.__priority_queue.pop(0)
            self._lazy_queue.remove(widget)
        elif self._lazy_queue:
            widget = self._lazy_queue.pop(0)
        if widget is not None:
            widget.connect("populated",
                           self._on_populated,
                           self.__lazy_loading_id)
            # https://gitlab.gnome.org/World/lollypop/issues/1884
            GLib.idle_add(widget.populate)
        else:
            self.__lazy_loading_id = None
            self.__is_populated = True
            Logger.debug("LazyLoadingView::lazy_loading(): %s",
                         time() - self.__start_time)

    def __is_visible(self, widget):
        """
            Is widget visible in scrolled
            @param widget as Gtk.Widget
        """
        widget_alloc = widget.get_allocation()
        scrolled_alloc = self._scrolled.get_allocation()
        try:
            (x, y) = widget.translate_coordinates(self._scrolled, 0, 0)
            return (y > -widget_alloc.height or y >= 0) and\
                y < scrolled_alloc.height
        except:
            return True

    def __lazy_or_not(self):
        """
            Add visible widgets to lazy queue
        """
        if self.__lazy_loading_id is None:
            return
        self.__scroll_timeout_id = None
        self.__priority_queue = []
        for child in self._lazy_queue:
            if self.__is_visible(child):
                self.__priority_queue.append(child)

    def __on_viewport_size_allocated(self, viewport, allocation):
        """
            Restore scrolled position
            @param viewport as Gtk.Viewport
            @param allocation as Gdk.Rectangle
        """
        if allocation.height > 1 and self.__scrolled_position is not None:
            self._viewport.disconnect_by_func(
                self.__on_viewport_size_allocated)
            self._scrolled.get_vadjustment().set_value(
                self.__scrolled_position)
            self.__scrolled_position = None
