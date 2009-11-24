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

import urllib
import pycurl

import oauth.oauth as oauth

REQUEST_TOKEN_URL = 'http://vimeo.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://vimeo.com/oauth/access_token'
AUTHORIZATION_URL = 'http://vimeo.com/oauth/authorize'

PORT=80

class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, server, port=PORT, request_token_url=REQUEST_TOKEN_URL, 
                 access_token_url=ACCESS_TOKEN_URL, authorization_url=AUTHORIZATION_URL):
        self.server = server
        self.port = PORT
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
##        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))

        self.buf = None

    def body_callback(self, buf):
        self.buf += buf

    def do_request(self, url):
        self.buf = ""
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, self.body_callback)
        curl.perform()
        curl.close()
        p = self.buf
        self.buf = ""
        return p


    def fetch_request_token(self, oauth_request):
        ans = self.do_request(oauth_request.to_url())
        return oauth.OAuthToken.from_string(ans)
