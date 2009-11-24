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
import xml.etree.ElementTree as ET
import inspect

import oauth.oauth as oauth

REQUEST_TOKEN_URL = 'http://vimeo.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://vimeo.com/oauth/access_token'
AUTHORIZATION_URL = 'http://vimeo.com/oauth/authorize'

API_REST_CALL_URL = 'http://vimeo.com/api/rest/v2/'
API_V2_CALL_URL = 'http://vimeo.com/api/v2/'

PORT=80

HMAC_SHA1 = oauth.OAuthSignatureMethod_HMAC_SHA1()


class VimeoException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    
    def __str__(self):
        return self.msg

class CurlyRestException(Exception):
    def __init__(self, code, msg, full):
        Exception.__init__(self)
        self.code = code
        self.msg = msg
        self.full = full

    def __str__(self):
        return "Error code: %s, message: %s\nFull message: %s" % (self.code, 
                                                                  self.msg, 
                                                                  self.full)


class CurlyRequest:
    def __init__(self, pbarsize=19):
        self.buf = None
        self.pbar_size = pbarsize
        self.pidx = 0

    def do_rest_call(self, url):
        res = self.do_request(url)
        try:
            t = ET.fromstring(res)

            if t.attrib['stat'] == 'fail':
                err_code = t.find('err').attrib['code']
                err_msg = t.find('err').attrib['msg']
                raise CurlyRestException(err_code, err_msg, ET.tostring(t))
            return t
        except Exception,e:
            print "Error with:", res
            raise e

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
    
    def upload_progress(self, download_t, download_d, upload_t, upload_d):
        # this is only for upload progress bar
	if upload_t == 0:
            return 0

        self.pidx = (self.pidx + 1) % len(TURNING_BAR)

        done = int(self.pbar_size * upload_d / upload_t)

        if done != self.pbar_size:
            pstr = '#'*done  +'>' + ' '*(self.pbar_size - done - 1)
        else:
            pstr = '#'*done

        print "\r%s[%s]  " %(TURNING_BAR[self.pidx], pstr),
        return 0
        
    def do_post_call(self, url, args, use_progress=False):
        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        c.setopt(c.URL, url)
        c.setopt(c.HTTPPOST, args)
        c.setopt(c.WRITEFUNCTION, self.body_callback)
        #c.setopt(c.VERBOSE, 1)
        self.buf = ""

        c.setopt(c.NOPROGRESS, 0)
        
        if use_progress:
            c.setopt(c.PROGRESSFUNCTION, self.upload_progress)

        c.perform()
        c.close()
        res = self.buf
        self.buf = ""
        return res

class SimpleOAuthClient(oauth.OAuthClient):

    def __init__(self, key, secret,
                 server="vimeo.com", port=PORT, 
                 request_token_url=REQUEST_TOKEN_URL, 
                 access_token_url=ACCESS_TOKEN_URL, 
                 authorization_url=AUTHORIZATION_URL):
        self.curly = CurlyRequest()
        self.key = key
        self.secret = secret
        self.server = server
        self.port = PORT
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url

        self.consumer = None
        self.token = None
##        self.connection = httplib.HTTPConnection("%s:%d" % (self.server, self.port))


    def get_token(self):
        self.consumer = oauth.OAuthConsumer(self.key, self.secret)
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                   http_url=self.request_token_url)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, None)
        print 'parameters: %s' % str(oauth_request.parameters)
        self.token = self.fetch_request_token(oauth_request)
        print "Token:", self.token


    def authorize_token(self, oauth_request):
        # via url
        # -> typically just some okay response
        print oauth_request.to_url()
##        return self.do_request(oauth_request.to_url())

    def fetch_request_token(self, oauth_request):
        ans = self.curly.do_request(oauth_request.to_url())
        return oauth.OAuthToken.from_string(ans)

    def vimeo_oauth_checkAccessToken(self, auth_token):
        pass

    def vimeo_videos_upload_getQuota(self):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   token=self.token,
                                                                   http_method='GET',
                                                                   http_url=API_REST_CALL_URL,
                                                                   parameters={'method': "vimeo.videos.upload.getQuota"})
        oauth_request.sign_request(HMAC_SHA1, self.consumer, self.token)

        self.curly.do_rest_call(oauth_request.to_url())
    

def _simple_request(url, format):
    if format != 'xml':
        raise VimeoException("Sorry, only 'xml' supported. '%s' was requested." %format)

    curly = CurlyRequest()
    url = url %(format)
    ans = curly.do_request(url)

    if format == 'xml':
        return ET.fromstring(ans)

##
## User related call from the "Simple API".
## See : http://vimeo.com/api/docs/simple-api
##

def _user_request(user, info, format):
    url = API_V2_CALL_URL + '%s/%s.%%s' %(user,info)
    return _simple_request(url, format)

def user_info(user, format="xml"):
    """
    User info for the specified user
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)


def user_videos(user, format="xml"):
    """
    Videos created by user
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_likes(user, format="xml"):
    """
    Videos the user likes
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_appears_in(user, format="xml"):
    """
    Videos that the user appears in
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_all_videos(user, format="xml"):
    """
    Videos that the user appears in and created
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_subscriptions(user, format="xml"):
    """
    Videos the user is subscribed to
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_albums(user, format="xml"):
    """
    Albums the user has created
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_channels(user, format="xml"):
    """
    Channels the user has created and subscribed to
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_groups(user, format="xml"):
    """
    Groups the user has created and joined
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_contacts_videos(user, format="xml"):
    """
    Videos that the user's contacts created
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)

def user_contacts_like(user, format="xml"):
    """
    Videos that the user's contacts like
    """
    return _user_request(user, inspect.stack()[0][3][5:], format)


##
## get a specific video
##
def video_request(video, format):
    url = API_V2_CALL_URL + 'video/%s.%%s' %(video)
    return _simple_request(url)

