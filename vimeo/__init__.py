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
    ## untested
    def vimeo_albums_addVideo(self, album_id, video_id):
        """
        Add a video to an album. 

        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'video_id': video_id}
        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params)

    ## untested
    def vimeo_albums_create(self, title, video_id, 
                            description=None, videos=[]):
        """
        Create an album. 

        Returns album id
        """
        params = {'title': title,
                  'video_id': video_id}
        if description != None:
            params['description'] = description
        if videos != []:
            params['videos'] = ','.join(videos)

        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 

    ## untested
    def vimeo_albums_delete(self, album_id):
        """
        Permanently delete an album. 

        This method returns an empty success response.
        """
        params = {'album_id': album_id}
        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 
        
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
    ## untested
    def vimeo_albums_getVideos(self, album_id, full_response=None,
                               page=None, password=None, per_page=None):
        """
        Get a list of the videos in an album.
        """

        params = {'album_id' : album_id}
        if full_response != None:
            params['full_response'] = full_response
        if page != None:
            params['page'] = page
        if password != None:
            params['password'] = password
        if per_page != None:
            params['per_page'] = per_page

        return self._do_vimeo_unauthenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                   parameters=params)
    ## untested
    def vimeo_albums_removeVideo(self, album_id, video_id=None):
        """
        Remove a video from an album.

        This method returns an empty success response.
        """
        params = {'album_id' : album_id}
        if video_id != None:
            params['video_id'] = video_id

        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 

    ## untested
    def vimeo_albums_setDescription(self, album_id, description):
        """
        Set the description for an album, overwriting the previous
        description.
        
        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'description': description}

        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 

    ## untested
    def vimeo_albums_setPassword(self, album_id, password):
        """
        Set or clear the password for an album.

        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'password': password}

        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 

    ## untested
    def vimeo_albums_setTitle(self, album_id, title):
        """
        Set the title of an album, overwriting the previous title.
        
        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'title': title}

        return self._do_vimeo_authenticated_call(inspect.stack()[0][3].replace('_', '.'),
                                                 parameters=params) 

        
###
### Channel section
###


# vimeo.channels.addVideo
# Add a video to a channel.	

# You can only add a video to a channel if you're the moderator of that channel.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# channel_id (required)
# The numeric id of the channel or its url name.
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The ID of the video.
# Example Responses

# This method returns an empty success response.


# vimeo.channels.getInfo
# Get the information on a single channel.
# Authentication

# This method does not require authentication.

# API Parameters

# channel_id (required)
# The numeric id of the channel or its url name.


# vimeo.channels.getModerators
# Get a list of the channel's moderators.
# Authentication

# This method does not require authentication.

# API Parameters

# channel_id (required)
# The numeric id of the channel or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.

# vimeo.channels.getSubscribers
# Get a list of the channel's subscribers.
# Authentication

# This method does not require authentication.

# API Parameters

# channel_id (required)
# The numeric id of the channel or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.

# vimeo.channels.getVideos
# Get a list of the videos in a channel.
# Authentication

# This method does not require authentication.

# API Parameters

# channel_id (required)
# The numeric id of the channel or its url name.
# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.


# vimeo.channels.removeVideo
# Remove a video from a channel.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# channel_id (optional)
# The numeric id of the channel or its url name.
# oauth_token (required)
# The access token for the acting user.
# video_id (optional)
# The ID of the video.
# Example Responses

# This method returns an empty success response.


# vimeo.channels.subscribe
# Subscribe a user to a channel.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# channel_id (optional)
# The numeric id of the channel or its url name.
# oauth_token (required)
# The access token for the acting user.
# Example Responses

# This method returns an empty success response.

# vimeo.channels.unsubscribe
# Unsubscribe a user from a channel.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# channel_id (optional)
# The numeric id of the channel or its url name.
# oauth_token (required)
# The access token for the acting user.
# Example Responses

# This method returns an empty success response.


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

# vimeo.contacts.getAll
# Get a list of contacts for a specified user.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, alphabetical, or most_credited.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.contacts.getMutual
# Get a list of the mutual contacts of a specific user.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.
# user_id (required)
# The user. Can either be ID number or username. A token can also be used instead of this parameter.


# vimeo.contacts.getOnline
# Get a list of the user's contacts who are currently online.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of online contacts to show on each page. Max 50.


# vimeo.contacts.getWhoAdded
# Get a list of the users who have added a specific user as a contact.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, alphabetical, or most_credited.
# user_id (required)
# The user. Can either be ID number or username. A token can also be used instead of this parameter.


# vimeo.groups.addVideo
# Add a video to a group.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# group_id (required)
# The group to add the video to. The user must be joined to the group. This can be either the ID of the group, or the name in the URL.
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The ID of the video to add to the group.
# Example Responses

# This method returns an empty success response.


# vimeo.groups.getAll
# Get a list of all public groups.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of groups to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, alphabetical, most_videos, most_subscribed, or most_recently_updated.


# vimeo.groups.getFiles
# Get a list of files uploaded to a group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.


# vimeo.groups.getInfo
# Get information for a specific group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.


# vimeo.groups.getMembers
# Get a list of the members of a group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, or alphabetical.

# vimeo.groups.getModerators
# Get a list of the group's moderators.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.

# vimeo.groups.getVideoComments
# Get a list of the comments on a video in a group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of comments to show on each page. Max 50.
# video_id (required)
# The ID of the video.

# vimeo.groups.getVideos
# Get a list of the videos added to a group.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, featured, most_played, most_commented, most_liked, or random.


# vimeo.groups.join
# Join a group.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# group_id (optional)
# The numeric id of the group or its url name.
# oauth_token (required)
# The access token for the acting user.
# Example Responses

# This method returns an empty success response.

# vimeo.groups.leave
# Leave a group.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# group_id (optional)
# The numeric id of the group or its url name.
# oauth_token (required)
# The access token for the acting user.
# Example Responses

# This method returns an empty success response.


# vimeo.groups.events.getMonth
# Get events from a group in a specific month.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# month (optional)
# The month to get events from. Defaults to the current month.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of events to show on each page. Max 50.
# year (optional)
# The year to get events from. Defaults to the current year.


# vimeo.groups.events.getPast
# Get all past events from a group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of events to show on each page. Max 50.


# vimeo.groups.events.getUpcoming
# Get all upcoming events from a group.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of events to show on each page. Max 50.


# vimeo.groups.forums.getTopicComments
# Get a list of comments in a group forum topic.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of comments to show on each page. Max 50.
# topic_id (required)
# The group forum topic ID.

# vimeo.groups.forums.getTopics
# Get a list of topics in a group forum.
# Authentication

# This method does not require authentication.

# API Parameters

# group_id (required)
# The numeric id of the group or its url name.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.

# vimeo.oauth.checkAccessToken
# Return the credentials attached to an Access Token.
# Authentication

# This method does not require authentication.

# API Parameters

# oauth_token (required)
# The access token for the user.

# vimeo.oauth.convertAuthToken
# Convert an old auth token to an OAuth Access Token.	

# After you call this method the old auth token will no longer be valid.
# Authentication

# This method does not require authentication.

# API Parameters

# auth_token (required)
# The old auth token

# vimeo.videos.addCast
# Add a specified user as a cast member to the video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# role (optional)
# The role of the user in the video.
# user_id (required)
# The user to add as a cast member.
# video_id (required)
# The video to add the cast member to.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.addPhotos
# Add Flickr photos to a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# photo_urls (required)
# A comma-separated list of Flickr photo urls.
# video_id (required)
# The video to add photos to.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.addTags
# Add tags to a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# tags (required)
# A comma-separated list of tags to add to the video.
# video_id (required)
# The video to add tags to.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.clearTags
# Remove all of the tags from a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The video to remove the tags from.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.delete
# Permanently delete a video.
# Authentication

# This method requires authentication with delete permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The video to permanently delete.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.getAll
# Get all videos credited to a user (both uploaded and appears).
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.


# vimeo.videos.getAppearsIn
# Get a list of videos that a user appears in.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.


# vimeo.videos.getByTag
# Get a list of videos that have the specified tag.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, most_liked, or relevant.
# tag (required)
# The tag.

# vimeo.videos.getCast
# Get the cast members of a video.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of users to show on each page. Max 50.
# video_id (required)
# The ID of the video.

# vimeo.videos.getContactsLiked
# Get a list of the videos liked by the user's contacts.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.videos.getContactsUploaded
# Get a list of the videos uploaded by the user's contacts.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.videos.getInfo
# Get lots of information on a video.
# Authentication

# This method does not require authentication.

# API Parameters

# video_id (required)
# The ID of the video.

# vimeo.videos.getLikes
# Get a list of videos that the user likes.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.videos.getSourceFileUrls
# Get a list of the source files for a video.	

# Authentication

# This method does not require authentication.

# API Parameters

# video_id (required)
# The ID of the video.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.getSubscriptions
# Get a list of the subscribed videos for a user.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.videos.getThumbnailUrls
# Get the URLs of a video's thumbnails.
# Authentication

# This method does not require authentication.

# API Parameters

# video_id (required)
# The ID of the video.

# vimeo.videos.getUploaded
# Get a list of videos uploaded by a user.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# sort (optional)
# Method to sort by: newest, oldest, most_played, most_commented, or most_liked.
# user_id (required)
# The ID number or username of the user. A token may be used instead.

# vimeo.videos.removeCast
# Remove a cast member from a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# user_id (required)
# The user to remove from the cast.
# video_id (required)
# The video to remove the cast member from.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.removeTag
# Remove a tag from a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# tag_id (required)
# The ID of the tag to remove from the video.
# video_id (required)
# The video to remove the tag from.
# Example Responses

# This method returns an empty success response.


# vimeo.videos.search
# Search for videos.
# Authentication

# This method does not require authentication.

# API Parameters

# full_response (optional)
# Set this parameter to get back the full video information.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of videos to show on each page. Max 50.
# query (required)
# The search terms
# sort (optional)
# Method to sort by: relevant, newest, oldest, most_played, most_commented, or most_liked.
# user_id (optional)
# The ID number or username of the user.

# vimeo.videos.setDescription
# Set the description for a video, overwriting the previous description.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# description (required)
# The new description (can be blank).
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The ID of the video.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.setLike
# Set whether or not the user likes a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# like (required)
# If this is true, we will record that the user likes this video. If false, we will remove it from their liked videos.
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The ID of the video to like.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.setPrivacy
# Set the privacy of a video. The possible privacy settings are anybody, nobody, contacts, users, password, or disable.
# anybody - anybody can view the video
# nobody - only the owner can view the video
# contacts - only the owner's contacts can view the video
# users - only specific users can view the video
# password - the video will require a password
# disable  - the video will not appear on Vimeo.com at all
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# password (optional)
# The password to protect the video with.
# privacy (required)
# The privacy setting to use.
# users (optional)
# A comma-separated list of users who can view the video.
# video_id (required)
# The ID of the video.

# vimeo.videos.setTitle
# Sets the title of a video, overwriting the previous title.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# title (required)
# The new title. If left blank, title will be set to "Untitled".
# video_id (required)
# The ID of the video.

# vimeo.videos.comments.addComment
# Add a comment to a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# comment_text (required)
# The text of the comment.
# oauth_token (required)
# The access token for the acting user.
# reply_to_comment_id (optional)
# If this is a reply to another comment, include that comment's ID.
# video_id (required)
# The video to comment on.


# vimeo.videos.comments.deleteComment
# Delete a specific comment from a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# comment_id (required)
# The ID of the comment to delete.
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The video that has the comment.

# vimeo.videos.comments.editComment
# Edit the text of a comment posted to a video.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# comment_id (required)
# The comment to edit.
# comment_text (required)
# The new text of the comment.
# oauth_token (required)
# The access token for the acting user.
# video_id (required)
# The video that has the comment.

# vimeo.videos.comments.getList
# Get a list of the comments on a video.
# Authentication

# This method does not require authentication.

# API Parameters

# page (optional)
# The page number to show.
# per_page (optional)
# Number of comments to show on each page. Max 50.
# video_id (required)
# The ID of the video.

# vimeo.videos.embed.getPresets	 
# Get the available embed presets for a user.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# page (optional)
# The page number to show.
# per_page (optional)
# Number of presets to show on each page. Max 50.


# vimeo.videos.embed.setPreset	 
# Set the embed preferences of a video using an embed preset.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# preset_id (required)
# The embed preset ID
# video_id (optional)
# The ID of the video.
# Example Responses

# This method returns an empty success response.

# vimeo.videos.upload.checkTicket
# Check to make sure an upload ticket is still valid.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.
# ticket_id (required)
# The upload ticket


# vimeo.videos.upload.confirm
# Complete the upload process.	

# If you uploaded only one chunk, you may skip passing a manifest, but if you uploaded multiple files, you must POST a manifest to this method. You can use either an XML or JSON formatted manifest. The manifest should not be included in the signature.
# Authentication

# This method requires authentication with read permission.

# API Parameters

# filename (optional)
# optional The name of the file, including extension
# json_manifest (optional)
# optional The JSON-encoded manifest
# oauth_token (required)
# The access token for the acting user.
# ticket_id (required)
# The upload ticket
# xml_manifest (optional)
# optional The XML-formatted manifest


# vimeo.videos.upload.getQuota
# Get the space and number of HD uploads left for a user.	

# Numbers are provided in bytes. It's a good idea to check this method before you upload a video to let the user know if their video will be converted to HD. hd_quota will have a value of 0 if the user reached the max number of uploads, 1 otherwise. Resets is the number of the day of the week, starting with Sunday.
# Authentication

# This method requires authentication with read permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.


# vimeo.videos.upload.getTicket
# Generate a new upload ticket. This ticket is good for one upload by one user.	

# Once you have the endpoint and the ticket id, you can conduct successive POSTs to the endpoint. You can POST the entire file or break it into pieces and post each one into a field called "file_data". After each post, the server will return an unformatted MD5 of the uploaded file. If this does not match what you uploaded, you can upload again and choose not to use this piece later when recombining pieces. This will allow you to build an uploader capable of resuming if the connection dies.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# oauth_token (required)
# The access token for the acting user.

# vimeo.videos.upload.verifyManifest
# Verify and combine any pieces uploaded.	

# Once the video is uploaded you must provide the MD5s of each piece that was uploaded. If you uploaded several pieces, the order of the pieces in the list dictates the order in which they will be combined. The server will return the MD5 of the entire file, and a list of the MD5s of any files that you uploaded but did not include in the manifest. You can use either an XML or JSON formatted manifest. It should not be included in the signature.
# Authentication

# This method requires authentication with write permission.

# API Parameters

# json_manifest (required)
# The JSON-encoded manifest
# oauth_token (required)
# The access token for the acting user.
# ticket_id (required)
# The upload ticket
# xml_manifest (required)
# The XML-formatted manifest



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

