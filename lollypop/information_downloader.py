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

from gi.repository import GLib

import json
from locale import getdefaultlocale

from lollypop.define import App, AUDIODB_CLIENT_ID
from lollypop.utils import get_network_available
from lollypop.logger import Logger
from lollypop.wikipedia import Wikipedia


class InformationDownloader:
    """
        Download info from the web
    """

    def __init__(self):
        """
            Init info downloader
        """
        pass

    def get_information(self, artist, callback, *args):
        """
            Get artist information
            @param artist as str
            @param callback as function
        """
        if not get_network_available("DATA"):
            callback(None, *args)
            return
        App().task_helper.run(self.__get_information, artist, callback, *args)

#######################
# PROTECTED           #
#######################
    def _get_audiodb_artist_info(self, artist):
        """
            Get artist info from audiodb
            @param artist as str
            @return info as bytes
        """
        if not get_network_available("AUDIODB"):
            return None
        try:
            artist = GLib.uri_escape_string(artist, None, True)
            uri = "https://theaudiodb.com/api/v1/json/"
            uri += "%s/search.php?s=%s" % (AUDIODB_CLIENT_ID, artist)
            (status, data) = App().task_helper.load_uri_content_sync(uri, None)
            if status:
                decode = json.loads(data.decode("utf-8"))
                language = getdefaultlocale()[0][-2:]
                for item in decode["artists"]:
                    for key in ["strBiography%s" % language,
                                "strBiographyEN"]:
                        info = item[key]
                        if info is not None:
                            return info.encode("utf-8")
        except Exception as e:
            Logger.error("InfoDownloader::_get_audiodb_artist_info: %s, %s" %
                         (e, artist))
        return None

    def _get_lastfm_artist_info(self, artist):
        """
            Get artist info from audiodb
            @param artist as str
            @return info as bytes
        """
        info = None
        try:
            if App().lastfm is not None and get_network_available("LASTFM"):
                info = App().lastfm.get_artist_bio(artist)
        except Exception as e:
            Logger.error("InfoDownloader::_get_lastfm_artist_info(): %s" % e)
        return info

#######################
# PRIVATE             #
#######################
    def __get_information(self, artist, callback, *args):
        """
            Get information for artist
            @param artist as str
            @param callback as function
        """
        content = None
        try:
            # Try from Wikipedia first
            if get_network_available("WIKIPEDIA"):
                wikipedia = Wikipedia()
                content = wikipedia.get_content_for_term(artist)
            if content is None:
                for method in [self._get_audiodb_artist_info,
                               self._get_lastfm_artist_info]:
                    content = method(artist)
                    if content is not None:
                        break
            callback(content, *args)
        except Exception as e:
            Logger.info("InfoDownloader::__get_information(): %s" % e)