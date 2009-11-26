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


"""
Python module to interact with Vimeo through its API (version 2)
"""

import urllib
import pycurl
import xml.etree.ElementTree as ET
import inspect
##from oauth import OAuthRequest, OAuthToken
import oauth.oauth as oauth

REQUEST_TOKEN_URL = 'http://vimeo.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://vimeo.com/oauth/access_token'
AUTHORIZATION_URL = 'http://vimeo.com/oauth/authorize'

API_REST_URL = 'http://vimeo.com/api/rest/v2/'
API_V2_CALL_URL = 'http://vimeo.com/api/v2/'

USER_AGENT = 'python-vimeo http://github.com/dkm/python-vimeo'

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
    """
    A CurlyRequest object is used to send HTTP requests.
    It's a simple wrapper around basic curl methods.
    In particular, it can upload files and display a progress bar.
    """
    def __init__(self, pbarsize=19):
        self.buf = None
        self.pbar_size = pbarsize
        self.pidx = 0

    def do_rest_call(self, url):
        """
        Send a simple GET request and interpret the answer as a REST reply.
        """

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

    def _body_callback(self, buf):
        self.buf += buf

    def do_request(self, url):
        """
        Send a simple GET request
        """
        self.buf = ""
        curl = pycurl.Curl()
        curl.setopt(pycurl.USERAGENT, USER_AGENT)
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, self._body_callback)
        curl.perform()
        curl.close()
        p = self.buf
        self.buf = ""
        return p
    
    def _upload_progress(self, download_t, download_d, upload_t, upload_d):
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
        """
        Send a simple POST request
        """
        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        c.setopt(c.URL, url)
        c.setopt(c.HTTPPOST, args)
        c.setopt(c.WRITEFUNCTION, self.body_callback)
        #c.setopt(c.VERBOSE, 1)
        self.buf = ""

        c.setopt(c.NOPROGRESS, 0)
        
        if use_progress:
            c.setopt(c.PROGRESSFUNCTION, self._upload_progress)

        c.perform()
        c.close()
        res = self.buf
        self.buf = ""
        return res

class SimpleOAuthClient(oauth.OAuthClient):
    """
    Class used for handling authenticated call to the API.
    """

    def __init__(self, key, secret,
                 server="vimeo.com", port=PORT, 
                 request_token_url=REQUEST_TOKEN_URL, 
                 access_token_url=ACCESS_TOKEN_URL, 
                 authorization_url=AUTHORIZATION_URL,
                 token=None,
                 token_secret=None):
        """
        You need to give both key (consumer key) and secret (consumer secret).
        If you already have an access token (token+secret), you can use it
        by giving it through token and token_secret parameters.
        If not, then you need to call both get_request_token(), get_authorize_token_url() and 
        finally get_access_token().
        """

        self.curly = CurlyRequest()
        self.key = key
        self.secret = secret
        self.server = server
        self.port = PORT
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.consumer = oauth.OAuthConsumer(self.key, self.secret)

        if token != None and token_secret != None:
            self.token = oauth.OAuthToken(token, token_secret)
        else:
            self.token = None
        
    def get_request_token(self):
        """
        Requests a request token and return it on success.
        """
        oauth_request = oauth.OAuthToken.from_consumer_and_token(self.consumer, 
                                                                 http_url=self.request_token_url)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, None)
        self.token = self._fetch_token(oauth_request)


    def get_authorize_token_url(self):
        """
        Returns a URL used to verify and authorize the application to access
        user's account. The pointed page should contain a simple 'password' that
        acts as the 'verifier' in oauth.
        """

        oauth_request = oauth.OAuthToken.from_token_and_callback(token=self.token, 
                                                                 http_url=self.authorization_url)
        return oauth_request.to_url()


    def get_access_token(self, verifier):
        """
        Should be called after having received the 'verifier' from the authorization page.
        See 'get_authorize_token_url()' method.
        """

        self.token.set_verifier(verifier)
        oauth_request = oauth.OAuthToken.from_consumer_and_token(self.consumer, 
                                                                 token=self.token, 
                                                                 verifier=verifier, 
                                                                 http_url=self.access_token_url)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, self.token)
        self.token = self._fetch_token(oauth_request)

    def _fetch_token(self, oauth_request):
        """
        Sends a requests and interprets the result as a token string.
        """
        ans = self.curly.do_request(oauth_request.to_url())
        return oauth.OAuthToken.from_string(ans)

    def vimeo_oauth_checkAccessToken(self, auth_token):
        pass


    def _do_vimeo_authenticated_call(self, method, parameters={}):
        """
        Wrapper to send an authenticated call to vimeo. You first need to have
        an access token.
        """

        parameters['method'] = method
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                 token=self.token,
                                                                 http_method='GET',
                                                                 http_url=API_REST_URL,
                                                                 parameters=parameters)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, self.token)
        return self.curly.do_rest_call(oauth_request.to_url())
        
    def _do_vimeo_unauthenticated_call(self, method, parameters={}):
        """
        Wrapper to send an unauthenticated call to vimeo. You don't need to have
        an access token.
        """
        parameters['method'] = method
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                 http_method='GET',
                                                                 http_url=API_REST_URL,
                                                                 parameters=parameters)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, None)
        return self.curly.do_rest_call(oauth_request.to_url())
###
### Album section
###
    def  vimeo_albums_getAll(self, user_id, sort=None,
                             per_page=None,
                             page=None):
        """
        Get a list of a user's albums.
        This method does not require authentication. 
        """
        params = {'user_id': user_id}
        if sort in ('newest', 'oldest', 'alphabetical'):
            params['sort'] = sort
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_unauthenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                   parameters=params)

###
### Channel section
###
    def vimeo_channels_getAll(self, sort=None,
                              per_page=None,
                              page=None):
        """
        Get a list of all public channels. 
        This method does not require authentication. 
        """
        params = {}
        if sort in ('newest', 'oldest', 'alphabetical', 
                    'most_videos', 'most_subscribed', 
                    'most_recently_updated'):
            params['sort'] = sort
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_unauthenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                   parameters=params)


###
### Contacts section
###


###
### Groups section
###

###
### Groups Events section
###

###
### Groups forums section
###

###
### OAuth section
###

###
### People section
###

###
### Test section
###
    def vimeo_test_echo(self, params={}):
        """
        This will just repeat back any parameters that you send. 
        No auth required
        """
        ## for simplicity, I'm using a signed call, but it's
        ## useless. Tokens & stuff will simply get echoed as the
        ## others parameters are.
        return self._do_vimeo_unauthenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                   parameters=params)


    def vimeo_test_login(self):
        """
        Is the user logged in? 
        """
        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'))


    def vimeo_test_null(self):
        """
        This is just a simple null/ping test.

        You can use this method to make sure that you are properly
        contacting to the Vimeo API.
        """
        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'))


###
### Videos section
###

###
### Videos comments section
###

###
### Videos embed section
###


###
### Videos Upload section
###

    def vimeo_videos_upload_getQuota(self):
        """
        (from vimeo API documentation)
        Get the space and number of HD uploads left for a user.

        Numbers are provided in bytes. It's a good idea to check this
        method before you upload a video to let the user know if their
        video will be converted to HD. hd_quota will have a value of 0
        if the user reached the max number of uploads, 1
        otherwise. Resets is the number of the day of the week,
        starting with Sunday.
        """
        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'))
    



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

