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

from gi.repository import Gio, GLib
from gi.repository.Gio import FILE_ATTRIBUTE_TIME_ACCESS

from time import time

from lollypop.logger import Logger
from lollypop.define import App


def is_audio(f):
    """
        Return True if files is audio
        @param f as Gio.File
    """
    audio = ["application/ogg", "application/x-ogg", "application/x-ogm-audio",
             "audio/aac", "audio/mp4", "audio/mpeg", "audio/mpegurl",
             "audio/ogg", "audio/vnd.rn-realaudio", "audio/vorbis",
             "audio/x-flac", "audio/x-mp3", "audio/x-mpeg", "audio/x-mpegurl",
             "audio/x-ms-wma", "audio/x-musepack", "audio/x-oggflac",
             "audio/x-pn-realaudio", "application/x-flac", "audio/x-speex",
             "audio/x-vorbis", "audio/x-vorbis+ogg", "audio/x-wav",
             "x-content/audio-player", "audio/x-aac", "audio/m4a",
             "audio/x-m4a", "audio/mp3", "audio/ac3", "audio/flac",
             "audio/x-opus+ogg", "application/x-extension-mp4", "audio/x-ape",
             "audio/x-pn-aiff", "audio/x-pn-au", "audio/x-pn-wav",
             "audio/x-pn-windows-acm", "application/x-matroska",
             "audio/x-matroska", "audio/x-wavpack", "video/mp4",
             "audio/x-mod", "audio/x-mo3", "audio/x-xm", "audio/x-s3m",
             "audio/x-it", "audio/aiff", "audio/x-aiff"]
    try:
        info = f.query_info("standard::content-type",
                            Gio.FileQueryInfoFlags.NONE)
        if info is not None:
            content_type = info.get_content_type()
            if content_type in audio:
                return True
    except Exception as e:
        Logger.error("is_audio: %s", e)
    return False


def is_pls(f):
    """
        Return True if files is a playlist
        @param f as Gio.File
    """
    try:
        info = f.query_info("standard::content-type",
                            Gio.FileQueryInfoFlags.NONE)
        if info is not None:
            if info.get_content_type() in ["audio/x-mpegurl",
                                           "application/xspf+xml"]:
                return True
    except:
        pass
    return False


def get_mtime(info):
    """
        Return Last modified time of a given file
        @param info as Gio.FileInfo
    """
    # Using time::changed is not reliable making lollypop doing a full
    # scan every two weeks (on my computer)
    # try:
    #    # We do not use time::modified because many tag editors
    #    # just preserve this setting
    #    return int(info.get_attribute_as_string("time::changed"))
    # except:
    #    pass
    return int(info.get_attribute_as_string("time::modified"))


def remove_oldest(path, timestamp):
    """
        Remove oldest files at path
        @param path as str
        @param timestamp as int
    """
    SCAN_QUERY_INFO = "%s" % FILE_ATTRIBUTE_TIME_ACCESS
    try:
        d = Gio.File.new_for_path(path)
        infos = d.enumerate_children(SCAN_QUERY_INFO,
                                     Gio.FileQueryInfoFlags.NONE,
                                     None)
        for info in infos:
            f = infos.get_child(info)
            if info.get_file_type() == Gio.FileType.REGULAR:
                atime = int(info.get_attribute_as_string(
                    FILE_ATTRIBUTE_TIME_ACCESS))
                # File not used since one year
                if time() - atime > timestamp:
                    f.delete(None)
    except Exception as e:
        Logger.error("remove_oldest(): %s", e)


def is_readonly(uri):
    """
        Check if uri is readonly
    """
    try:
        f = Gio.File.new_for_uri(uri)
        info = f.query_info("access::can-write",
                            Gio.FileQueryInfoFlags.NONE,
                            None)
        return not info.get_attribute_boolean("access::can-write")
    except:
        return True


def create_dir(path):
    """
        Create dir
        @param path as str
    """
    d = Gio.File.new_for_path(path)
    if not d.query_exists():
        try:
            d.make_directory_with_parents()
        except:
            Logger.info("Can't create %s" % path)


def install_youtube_dl():
    try:
        path = GLib.get_user_data_dir() + "/lollypop/python"
        argv = ["pip3", "install", "-t", path, "-U", "youtube-dl"]
        GLib.spawn_sync(None, argv, [], GLib.SpawnFlags.SEARCH_PATH, None)
    except Exception as e:
        Logger.error("install_youtube_dl: %s" % e)


def get_youtube_dl():
    """
        Get youtube-dl path and env
        @return (str, [])
    """
    if App().settings.get_value("recent-youtube-dl"):
        python_path = GLib.get_user_data_dir() + "/lollypop/python"
        path = "%s/bin/youtube-dl" % python_path
        env = ["PYTHONPATH=%s" % python_path]
        f = Gio.File.new_for_path(path)
        if f.query_exists():
            return (path, env)
    if GLib.find_program_in_path("youtube-dl"):
        return ("youtube-dl", [])
    else:
        return (None, [])


# From eyeD3 start
# eyeD3 is written and maintained by:
# Travis Shirk <travis@pobox.com>
def id3EncodingToString(encoding):
    from lollypop.define import LATIN1_ENCODING, UTF_8_ENCODING
    from lollypop.define import UTF_16_ENCODING, UTF_16BE_ENCODING
    if encoding == LATIN1_ENCODING:
        return "latin_1"
    elif encoding == UTF_8_ENCODING:
        return "utf_8"
    elif encoding == UTF_16_ENCODING:
        return "utf_16"
    elif encoding == UTF_16BE_ENCODING:
        return "utf_16_be"
    else:
        raise ValueError("Encoding unknown: %s" % encoding)


def decodeUnicode(bites, encoding):
    codec = id3EncodingToString(encoding)
    Logger.debug("Unicode encoding: %s" % codec)
    if (codec.startswith("utf_16") and
            len(bites) % 2 != 0 and bites[-1:] == b"\x00"):
        # Catch and fix bad utf16 data, it is everywhere.
        Logger.warning("Fixing utf16 data with extra zero bytes")
        bites = bites[:-1]
    return bites.decode(codec).rstrip("\x00")


def splitUnicode(data, encoding):
    from lollypop.define import LATIN1_ENCODING, UTF_8_ENCODING
    from lollypop.define import UTF_16_ENCODING, UTF_16BE_ENCODING
    try:
        if encoding == LATIN1_ENCODING or encoding == UTF_8_ENCODING:
            (d, t) = data.split(b"\x00", 1)
        elif encoding == UTF_16_ENCODING or encoding == UTF_16BE_ENCODING:
            # Two null bytes split, but since each utf16 char is also two
            # bytes we need to ensure we found a proper boundary.
            (d, t) = data.split(b"\x00\x00", 1)
            if (len(d) % 2) != 0:
                (d, t) = data.split(b"\x00\x00\x00", 1)
                d += b"\x00"
    except ValueError as ex:
        Logger.warning("Invalid 2-tuple ID3 frame data: %s", ex)
        d, t = data, b""
    return (d, t)
# From eyeD3 end