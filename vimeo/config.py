#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
# originaly part of 'plopifier'
#
# Plopifier is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Plopifier is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Plopifier.  If not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import os

DEFAULT_CONFIG="~/.python-vimeo.rc"

class VimeoConfig(ConfigParser.ConfigParser):
    def __init__(self, options=None):
        ConfigParser.ConfigParser.__init__(self)

        try:
            self.read(os.path.expanduser(DEFAULT_CONFIG))
        except IOError,e:
            # most probably the file does not exist
            if os.path.exists(os.path.expanduser(DEFAULT_CONFIG)):
                # looks like it's something else
                raise e
            # if not, simply ignore the error, config is empty

        if not options :
            return

        self.add_section("appli")
        self.add_section("auth")

        if options.key:
            self.set("appli", "consumer_key", options.key)

        if options.secret:
            self.set("appli", "consumer_secret", options.secret)

        if options.access_token:
            self.set("auth", "token", options.access_token)

        if options.access_token_secret:
            self.set("auth", "token_secret", options.access_token_secret)
