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

import xml.etree.ElementTree as ET
import inspect
import curl
import pycurl

import oauth.oauth as oauth

REQUEST_TOKEN_URL = 'http://vimeo.com/oauth/request_token'
ACCESS_TOKEN_URL = 'http://vimeo.com/oauth/access_token'
AUTHORIZATION_URL = 'http://vimeo.com/oauth/authorize'

API_REST_URL = 'http://vimeo.com/api/rest/v2/'
API_V2_CALL_URL = 'http://vimeo.com/api/v2/'

PORT=80

HMAC_SHA1 = oauth.OAuthSignatureMethod_HMAC_SHA1()

class VimeoException(Exception):
    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg
    
    def __str__(self):
        return self.msg


class VimeoOAuthClient(oauth.OAuthClient):
    """
    Class used for handling authenticated call to the API.
    """

    def __init__(self, key, secret,
                 server="vimeo.com", port=PORT, 
                 request_token_url=REQUEST_TOKEN_URL, 
                 access_token_url=ACCESS_TOKEN_URL, 
                 authorization_url=AUTHORIZATION_URL,
                 token=None,
                 token_secret=None,
                 verifier=None,
                 vimeo_config=None):
        """
        You need to give both key (consumer key) and secret (consumer secret).
        If you already have an access token (token+secret), you can use it
        by giving it through token and token_secret parameters.
        If not, then you need to call both get_request_token(), get_authorize_token_url() and 
        finally get_access_token().
        """

        self.curly = curl.CurlyRequest()
        self.key = key
        self.secret = secret
        self.server = server
        self.port = PORT
        self.request_token_url = request_token_url
        self.access_token_url = access_token_url
        self.authorization_url = authorization_url
        self.consumer = oauth.OAuthConsumer(self.key, self.secret)

        self.config = vimeo_config
        if self.config != None:
            try:
                token = self.config.get("auth", "token")
                token_secret = self.config.get("auth", "token_secret")
                verifier = self.config.get("auth", "verifier")
            except ConfigParser.NoSectionError, e:
                # not everything in config file. Simply skip
                pass

        if token != None and token_secret != None:
            self.token = oauth.OAuthToken(token, token_secret)
            self.token.set_verifier(verifier)
        else:
            self.token = None
        
    def get_request_token(self):
        """
        Requests a request token and return it on success.
        """
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                   http_url=self.request_token_url)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, None)
        self.token = self._fetch_token(oauth_request)


    def get_authorize_token_url(self, permission='read'):
        """
        Returns a URL used to verify and authorize the application to access
        user's account. The pointed page should contain a simple 'password' that
        acts as the 'verifier' in oauth.
        """

        oauth_request = oauth.OAuthRequest.from_token_and_callback(token=self.token, 
                                                                   http_url=self.authorization_url)
        return oauth_request.to_url() + "&permission=" + permission


    def get_access_token(self, verifier):
        """
        Should be called after having received the 'verifier' from the authorization page.
        See 'get_authorize_token_url()' method.
        """

        self.token.set_verifier(verifier)
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer, 
                                                                   token=self.token, 
                                                                   verifier=verifier, 
                                                                   http_url=self.access_token_url)
        oauth_request.sign_request(HMAC_SHA1, self.consumer, self.token)
        self.token = self._fetch_token(oauth_request)
        return self.token

    def _fetch_token(self, oauth_request):
        """
        Sends a requests and interprets the result as a token string.
        """
        ans = self.curly.do_request(oauth_request.to_url())
        return oauth.OAuthToken.from_string(ans)

    def _do_compute_vimeo_upload(self, endpoint, ticket_id):
        oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                   token=self.token,
                                                                   http_method='POST',
                                                                   http_url=endpoint,
                                                                   parameters={'ticket_id': ticket_id})
        oauth_request.sign_request(HMAC_SHA1, self.consumer, self.token)
        return oauth_request.parameters


    def do_upload(self, endpoint, ticket_id, filename):
        post_data = self._do_compute_vimeo_upload(endpoint, ticket_id)
        post_data['file_data'] = (pycurl.FORM_FILE, filename)
        # make sure everything is string !
        post_data_l = [(k,str(v)) for (k,v) in post_data.items()]

        self.curly.do_post_call(endpoint, post_data_l, True)

    def _do_vimeo_call(self, method, parameters={}, authenticated=True):
        """
        Wrapper to send a call to vimeo
        """
        parameters['method'] = method
        if authenticated:
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
                                                                       token=self.token,
                                                                       http_method='GET',
                                                                       http_url=API_REST_URL,
                                                                       parameters=parameters)
        else:
            oauth_request = oauth.OAuthRequest.from_consumer_and_token(self.consumer,
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
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
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

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 

    ## untested
    def vimeo_albums_delete(self, album_id):
        """
        Permanently delete an album. 

        This method returns an empty success response.
        """
        params = {'album_id': album_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 
        
    def vimeo_albums_getAll(self, user_id, sort=None,
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

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
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

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
    ## untested
    def vimeo_albums_removeVideo(self, album_id, video_id=None):
        """
        Remove a video from an album.

        This method returns an empty success response.
        """
        params = {'album_id' : album_id}
        if video_id != None:
            params['video_id'] = video_id

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
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

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 

    ## untested
    def vimeo_albums_setPassword(self, album_id, password):
        """
        Set or clear the password for an album.

        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'password': password}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 

    ## untested
    def vimeo_albums_setTitle(self, album_id, title):
        """
        Set the title of an album, overwriting the previous title.
        
        This method returns an empty success response.
        """
        params = {'album_id': album_id,
                  'title': title}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 

        
###
### Channel section
###

    ## untested
    def vimeo_channels_addVideo(self, channel_id, video_id):
        """
        Add a video to a channel.

        You can only add a video to a channel if you're the moderator
        of that channel.  

        This method returns an empty success response.
        """
        params = {'channel_id': channel_id,
                  'video_id': video_id}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 


    def vimeo_channels_getInfo(self, channel_id):
        """
        Get the information on a single channel.
        """
        params = {'channel_id': channel_id}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False) 

        
    def vimeo_channels_getModerators(self, channel_id, page=None, per_page=None):
        """
        Get a list of the channel's moderators.
        """
        params = {'channel_id': channel_id}
        if page != None:
            params = {'page': page}
        if per_page != None:
            params = {'per_page': per_page}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False) 



    def vimeo_channels_getSubscribers(self, channel_id, page=None, per_page=None):
        """
        Get a list of the channel's subscribers.
        """
        params = {'channel_id': channel_id}
        if page != None:
            params = {'page': page}
        if per_page != None:
            params = {'per_page': per_page}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False) 


    def vimeo_channels_getVideos(self, channel_id, full_response=None,
                                 page=None, per_page=None):
        """
        Get a list of the videos in a channel.
        """
        params = {'channel_id': channel_id}
        if page != None:
            params = {'page': page}
        if per_page != None:
            params = {'per_page': per_page}
        if full_response != None:
            params = {'full_response': full_response}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False) 

    def vimeo_channels_removeVideo(self, channel_id, video_id=None):
        """
        Remove a video from a channel.
        
        This method returns an empty success response.
        """
        params = {'channel_id': channel_id}
        if video_id != None:
            params['video_id'] = video_id

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 


    ## channel_id is optional in doc ?!
    def vimeo_channels_subscribe(self, channel_id):
        """
        Subscribe a user to a channel.

        This method returns an empty success response.
        """
        params = {'channel_id': channel_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 
        
    ## channel_id optional in doc ?!
    def vimeo_channels_unsubscribe(self, channel_id):
        """
        Unsubscribe a user from a channel.

        This method returns an empty success response.
        """
        params = {'channel_id': channel_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params) 


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

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


###
### Contacts section
###

    def vimeo_contacts_getAll(self, user_id,
                              page=None, per_page=None,
                              sort=None):
        """
        Get a list of contacts for a specified user.
        """
        params = {'user_id': user_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


    def vimeo_contacts_getMutual(self, user_id,
                                 page=None, per_page=None):
        """
        Get a list of the mutual contacts of a specific user.
        """

        params = {'user_id': user_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    def vimeo_contacts_getOnline(self, page=None, per_page=None):
        """
        Get a list of the user's contacts who are currently online.
        """
        params={}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    def vimeo_contacts_getWhoAdded(self, user_id,
                                   page=None, per_page=None,
                                   sort=None):
        """
        Get a list of the users who have added a specific user as a
        contact.
        """
        params={'user_id':user_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

###
### Groups section
###
        
    def vimeo_groups_addVideo(self, group_id, video_id):
        """
        Add a video to a group.

        This method returns an empty success response.
        """

        params={'group_id':group_id,
                'video_id': video_id}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)


    def vimeo_groups_getAll(self, page=None, per_page=None, sort=None):
        """
        Get a list of all public groups.
        """
        # Method to sort by: newest, oldest, alphabetical, most_videos,
        # most_subscribed, or most_recently_updated.

        params = {}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
        

    def vimeo_groups_getFiles(self, group_id, page=None, per_page=None):
        """
        Get a list of files uploaded to a group.
        """
        params = {'group_id':group_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


    def vimeo_groups_getInfo(self, group_id):
        """
        Get information for a specific group.
        """
        params = {'group_id':group_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    def vimeo_groups_getMembers(self, group_id, page=None, per_page=None,
                                sort=None):
        """
        Get a list of the members of a group.
        """

        # Method to sort by: newest, oldest, or alphabetical.
        params = {'group_id':group_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


    def vimeo_groups_getModerators(self, group_id, page=None, per_page=None):
        """
        Get a list of the group's moderators.
        """
        params = {'group_id':group_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
    
    def vimeo_groups_getVideoComments(self, group_id, video_id,
                                      page=None, per_page=None):
        """
        Get a list of the comments on a video in a group.
        """
        params = {'group_id':group_id}
        params = {'video_id':video_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


    def vimeo_groups_getVideos(self, group_id, full_response=None,
                               page=None, per_page=None, sort=None):
        """
        Get a list of the videos added to a group.
        """
        # Method to sort by: newest, oldest, featured,
        # most_played, most_commented, most_liked, or random.

        params = {'group_id':group_id}

        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    ## group_id optional in doc ?!
    def vimeo_groups_join(self, group_id):
        """
        Join a group.

        This method returns an empty success response.
        """
        params = {'group_id':group_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    ## group_id optional in doc ?!
    def vimeo_groups_leave(self, group_id):
        """
        Leave a group.

        This method returns an empty success response.
        """
        params = {'group_id':group_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)


###
### Groups Events section
###
    def vimeo_groups_events_getMonth(self, group_id, month=None, year=None,
                                     page=None, per_page=None):
        """
        Get events from a group in a specific month.
        """
        params = {'group_id':group_id}

        if month != None:
            params['month'] = month
        if year != None:
            params['year'] = year
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    def vimeo_groups_events_getPast(self, group_id, page=None, per_page=None):
        """
        Get all past events from a group.
        """
        params = {'group_id':group_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    def vimeo_groups_events_getUpcoming(self, group_id,
                                        page=None, per_page=None):
        """
        Get all upcoming events from a group.
        """
        params = {'group_id':group_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

###
### Groups forums section
###
    def vimeo_groups_forums_getTopicComments(self, group_id, topic_id,
                                             page=None, per_page=None):
        """
        Get a list of topics in a group forum.
        """
        params = {'group_id':group_id,
                  'topic_id':topic_id}

        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

###
### OAuth section
###

    ## this method does not need auth, but must include the token
    ## making an auth call should do the trick...
    def vimeo_oauth_checkAccessToken(self):
        """
        Return the credentials attached to an Access Token.
        """
        params={}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)
        
    ## this method does not need auth, but must include the token
    ## making an auth call should do the trick...
    ## I'm not sure this is correct
    def vimeo_oauth_convertAuthToken(self):
        """
        Convert an old auth token to an OAuth Access Token.  

        After you call this method the old auth token will no longer
        be valid.
        """
        params={}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

###
### Videos section
###

    def vimeo_videos_addCast(self, user_id, video_id, role=None):
        """
        Add a specified user as a cast member to the video.

        This method returns an empty success response. 
        """
        params={'user_id':user_id,
                'video_id':video_id}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)
    # oauth_token (required)
    # The access token for the acting user.
    # photo_urls (required)
    # A comma-separated list of Flickr photo urls.
    # video_id (required)
    # The video to add photos to.
    # Example Responses
    def vimeo_videos_addPhotos(self, photos_urls, video_id):
        """
        Add Flickr photos to a video.

        This method returns an empty success response.
        """
        params={'photos_urls':photos_urls,
                'video_id':video_id}

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)


    # oauth_token (required)
    # The access token for the acting user.
    # tags (required)
    # A comma-separated list of tags to add to the video.
    # video_id (required)
    # The video to add tags to.
    def vimeo_videos_addTags(self, tags, video_id):
        """
        Add tags to a video.

        This method returns an empty success response.
        """
        params={'tags':tags,
                'video_id':video_id}
        
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # video_id (required)
    # The video to remove the tags from.
    # Example Responses
    def vimeo_videos_clearTags(self, video_id):
        """
        Remove all of the tags from a video.

        This method returns an empty success response.
        """
        params={'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # video_id (required)
    # The video to permanently delete.
    def vimeo_videos_delete(self, video_id):
        """
        Permanently delete a video.

        This method returns an empty success response.
        """
        params={'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

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
    def vimeo_videos_getAll(self, user_id,
                            full_response=None, page=None,
                            per_page=None, sort=None):
        """
        Get all videos credited to a user (both uploaded and appears).
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


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
    def vimeo_videos_getAppearsIn(self, user_id,
                            full_response=None, page=None,
                            per_page=None, sort=None):
        """
        Get a list of videos that a user appears in.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

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
    def vimeo_videos_getByTag(self, tag, 
                            full_response=None, page=None,
                            per_page=None, sort=None):
        """
        Get a list of videos that have the specified tag.
        """
        params={'tag':tag}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # page (optional)
    # The page number to show.
    # per_page (optional)
    # Number of users to show on each page. Max 50.
    # video_id (required)
    # The ID of the video.
    def vimeo_videos_getCast(self, video_id,
                             page=None, per_page=None):
        """
        Get the cast members of a video.
        """
        params={'video_id':video_id}
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

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
    def vimeo_videos_getContactsLiked(self, user_id,
                                      full_response=None, page=None,
                                      per_page=None, sort=None):
        """
        Get a list of the videos liked by the user's contacts.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = page


        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


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
    def vimeo_videos_getContactsUploaded(self, user_id, 
                                         full_response=None, page=None,
                                         per_page=None, sort=None):
        """
        Get a list of the videos uploaded by the user's contacts.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # video_id (required)
    # The ID of the video.
    def vimeo_videos_getInfo(self, video_id):
        """
        Get lots of information on a video.
        """
        params={'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
        

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
    def vimeo_videos_getLikes(self, user_id,
                              full_response=None, page=None,
                              per_page=None, sort=None):
        """
        Get a list of videos that the user likes.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort

        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # video_id (required)
    # The ID of the video.
    # return empty array?!
    def vimeo_videos_getSourceFileUrls(self, video_id):
        """
        Get a list of the source files for a video.

        This method returns an empty success response.
        """
        params={'user_id':user_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

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
    def vimeo_videos_getSubscriptions(self, user_id,
                                      full_response=None, page=None,
                                      per_page=None, sort=None):
        """                                      
        Get a list of the subscribed videos for a user.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # video_id (required)
    # The ID of the video.
    def vimeo_videos_getThumbnailUrls(self, video_id):
        """
        Get the URLs of a video's thumbnails.
        """
        params={'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

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
    def vimeo_videos_getUploaded(self, user_id,
                                 full_response=None, page=None,
                                 per_page=None, sort=None):
        """
        Get a list of videos uploaded by a user.
        """
        params={'user_id':user_id}
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # user_id (required)
    # The user to remove from the cast.
    # video_id (required)
    # The video to remove the cast member from.
    # Example Responses
    def vimeo_videos_removeCast(self, user_id, video_id):
        """
        Remove a cast member from a video.
  
        This method returns an empty success response.
        """
        params={'user_id':user_id,
                'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # tag_id (required)
    # The ID of the tag to remove from the video.
    # video_id (required)
    # The video to remove the tag from.
    def vimeo_videos_removeTag(self, tag_id, video_id):
        """
        Remove a tag from a video.

        This method returns an empty success response.
        """
        params={'video_id':video_id,
                'tag_id':tag_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

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
    def vimeo_videos_search(self, query, user_id=None,
                            full_response=None, page=None,
                            per_page=None, sort=None):

        """
        Search for videos.
        """
        params={'query':query}
        if user_id != None:
            params['user_id'] = user_id
        if full_response != None:
            params['full_response'] = full_response
        if per_page != None:
            params['per_page'] = per_page
        if page != None:
            params['page'] = page
        if sort != None:
            params['sort'] = sort
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # description (required)
    # The new description (can be blank).
    # video_id (required)
    # The ID of the video.
    def vimeo_videos_setDescription(self, description, video_id):
        """
        Set the description for a video, overwriting the previous description.

        This method returns an empty success response.
        """
        params={'video_id':video_id,
                'description':description}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # like (required)
    # If this is true, we will record that the user likes this
    # video. If false, we will remove it from their liked videos.
    # oauth_token (required)
    # The access token for the acting user.
    # video_id (required)
    # The ID of the video to like.
    # Example Responses
    def vimeo_videos_setLike(self, like, video_id):
        """
        Set whether or not the user likes a video.

        This method returns an empty success response.
        """
        params={'video_id':video_id,
                'like': like}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # password (optional)
    # The password to protect the video with.
    # privacy (required)
    # The privacy setting to use.
    # users (optional)
    # A comma-separated list of users who can view the video.
    # video_id (required)
    # The ID of the video.
    def vimeo_videos_setPrivacy(self, privacy, video_id,
                                users=[], password=None):
        """
        Set the privacy of a video. The possible privacy settings are
        anybody, nobody, contacts, users, password, or disable.
        
        anybody - anybody can view the video
        nobody - only the owner can view the video
        contacts - only the owner's contacts can view the video
        users - only specific users can view the video
        password - the video will require a password
        disable  - the video will not appear on Vimeo.com at all
        """
        params={'video_id':video_id,
                'privacy':privacy}
        if users != []:
            params['users'] = ','.join(users)
        if password != None:
            params['passworrd'] = password
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # title (required)
    # The new title. If left blank, title will be set to "Untitled".
    # video_id (required)
    # The ID of the video.
    def vimeo_videos_setTitle(self, title, video_id):
        """
        Sets the title of a video, overwriting the previous title.
        """
        params={'video_id':video_id,
                'title':title}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

###
### Videos comments section
###

    # comment_text (required)
    # The text of the comment.
    # reply_to_comment_id (optional)
    # If this is a reply to another comment, include that comment's ID.
    # video_id (required)
    # The video to comment on.
    def vimeo_videos_comments_addComment(self, comment_text, video_id,
                                         reply_to_comment_id=None):
        """
        Add a comment to a video.
        """
        params={'comment_text':comment_text,
                'video_id':video_id}

        if reply_to_comment_id != None:
            params['reply_to_comment_id'] = reply_to_comment_id
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # comment_id (required)
    # The ID of the comment to delete.
    # video_id (required)
    # The video that has the comment.
    def vimeo_videos_comments_deleteComment(self, comment_id, video_id):
        """
        Delete a specific comment from a video.
        """
        params={'comment_id':comment_id,
                'video_id':video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)


    # comment_id (required)
    # The comment to edit.
    # comment_text (required)
    # The new text of the comment.
    # video_id (required)
    # The video that has the comment.
    def vimeo_videos_comments_editComment(self, comment_id,
                                          comment_text, video_id):
        """
        Edit the text of a comment posted to a video.
        """
        params = {'comment_id': comment_id,
                  'comment_text': comment_text,
                  'video_id': video_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # page (optional)
    # The page number to show.
    # per_page (optional)
    # Number of comments to show on each page. Max 50.
    # video_id (required)
    # The ID of the video.
    def vimeo_videos_comments_getList(self, video_id,
                                      page=None, per_page=None):
        """
        Get a list of the comments on a video.
        """
        params = {'video_id': video_id}
        if page != None:
            params['page'] = page
        if per_page != None:
            params['per_page'] = page
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

###
### Videos embed section
###

    # page (optional)
    # The page number to show.
    # per_page (optional)
    # Number of presets to show on each page. Max 50.
    def vimeo_videos_embed_getPresets(self, page=None, per_page=None):
        """
        Get the available embed presets for a user.
        """
        params = {}
        if page != None:
            params['page'] = page
        if per_page != None:
            params['per_page'] = page
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)
        
        

    # preset_id (required)
    # The embed preset ID
    # video_id (optional)
    # The ID of the video.
    # Example Responses
    def vimeo_videos_embed_setPreset(self, preset_id,
                                     video_id=None):
        """
        Set the embed preferences of a video using an embed preset.
        
        This method returns an empty success response.
        """
        params = {'preset_id': preset_id}
        if video_id != None:
            params['video_id'] = video_id
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)

    # ticket_id (required)
    # The upload ticket
    def vimeo_videos_upload_checkTicket(self, ticket_id):
        """
        Check to make sure an upload ticket is still valid.
        """
        params = {'ticket_id': ticket_id}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)

    # filename (optional)
    # optional The name of the file, including extension
    # json_manifest (optional)
    # optional The JSON-encoded manifest
    # ticket_id (required)
    # The upload ticket
    # xml_manifest (optional)
    # optional The XML-formatted manifest
    def vimeo_videos_upload_confirm(self, ticket_id,
                                    filename=None, json_manifest=None,
                                    xml_manifest=None):
        """                                    
        Complete the upload process.	
        
        If you uploaded only one chunk, you may skip passing a manifest, but
        if you uploaded multiple files, you must POST a manifest to this
        method. You can use either an XML or JSON formatted manifest. The
        manifest should not be included in the signature.
        """
        params = {'ticket_id': ticket_id}
        if filename != None:
            params['filename'] = filename
        if json_manifest != None:
            params['json_manifest'] = json_manifest
        if xml_manifest != None:
            params['xml_manifest'] = xml_manifest
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)



    def vimeo_videos_upload_getTicket(self):
        """
        Generate a new upload ticket. This ticket is good for one upload by
        one user.

        Once you have the endpoint and the ticket id, you can conduct
        successive POSTs to the endpoint. You can POST the entire file or
        break it into pieces and post each one into a field called
        "file_data". After each post, the server will return an unformatted
        MD5 of the uploaded file. If this does not match what you uploaded,
        you can upload again and choose not to use this piece later when
        recombining pieces. This will allow you to build an uploader capable
        of resuming if the connection dies.
        """
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'))
                                                 
    # json_manifest (required)
    # The JSON-encoded manifest
    # oauth_token (required)
    # The access token for the acting user.
    # ticket_id (required)
    # The upload ticket
    # xml_manifest (required)
    # The XML-formatted manifest
    def vimeo_videos_upload_verifyManifest(self, json_manifest, ticket_id, xml_manifest):
        """
        Verify and combine any pieces uploaded.	
        
        Once the video is uploaded you must provide the MD5s of each
        piece that was uploaded. If you uploaded several pieces, the
        order of the pieces in the list dictates the order in which
        they will be combined. The server will return the MD5 of the
        entire file, and a list of the MD5s of any files that you
        uploaded but did not include in the manifest. You can use
        either an XML or JSON formatted manifest. It should not be
        included in the signature.
        """
        params = {'json_manifest': json_manifest,
                  'ticket_id': ticket_id,
                  'xml_manifest': xml_manifest}
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params)
        
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
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'),
                                   parameters=params, authenticated=False)


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
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'))


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
        return self._do_vimeo_call(inspect.stack()[0][3].replace('_', '.'))
    



def _simple_request(url, format):
    if format != 'xml':
        raise VimeoException("Sorry, only 'xml' supported. '%s' was requested." %format)

    curly = curl.CurlyRequest()
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

