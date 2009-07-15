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
This module is used to interract with Vimeo through its API
Full documentation is available here:
 http://vimeo.com/api

This module will be used to upload video. Maybe it will
get more features as they are needed, but it's not the
current goal. Of course, any contribution is welcome !
"""

##import curl
import hashlib
import xml.etree.ElementTree as ET
import pycurl
import urllib
BASE_URL = "http://vimeo.com/api/rest"

TURNING_BAR='|/-\\'

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

class Vimeo:
    def __init__(self, apikey, apisecret, auth_token=None):
        self.apikey = apikey
        self.apisecret = apisecret
        self.frob = None
        self.auth_token = auth_token
        self.auth_perms = None
        self.user_dic = None
        self.curly = CurlyRequest()
        self.vimeo_bug_queue = []
        self.user_id = None


    def set_userid(self):
        (p,u) = self.auth_checkToken()
        self.user_id = u['id']

    def process_bug_queue(self):
        ok = []

        for i in self.vimeo_bug_queue:
            vid = i[0]
            title = i[1]
            tags = i[2]
            try :
                self.videos_setTitle(vid, title)
                self.videos_setPrivacy(vid)

                if len(tags) > 0:
                    self.videos_addTags(vid, tags)
                ok.append(i)
            except CurlyRestException,e:
                print "Still failing for video ", vid
        for i in ok:
            self.vimeo_bug_queue.remove(i)

    def get_url_sig(self, dic):
        tosig = self.apisecret
        url = "?"
        keys = dic.keys()
        keys.sort()
        for i in keys:
            tosig += i + dic[i]
            url += "%s=%s&" % (i, dic[i])

        m = hashlib.md5()
        m.update(tosig)
        sig = str(m.hexdigest())
        
        url += "api_sig="+sig
        return (url, sig)

    def getsig(self, method_name):
        m = hashlib.md5()
        l = "%sapi_key%smethod%s" % (self.apisecret, 
                                     self.apikey, 
                                     method_name)
        m.update(l)
        return m.hexdigest()

    def get_auth_url(self, perms="read"):
        if self.frob == None:
            raise VimeoException()

        burl = "http://vimeo.com/services/auth/" 
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'perms' : perms,
                                       'frob' : self.frob})
        return burl+url


    def do_upload(self, video, title, ticket=None, tags=[]):
        if self.auth_token == None:
            raise VimeoException()

        if ticket != None:
            upload_ticket = ticket
        else:
            upload_ticket = self.videos_getUploadTicket()

        self.upload(video, upload_ticket)

        vid = self.videos_checkUploadStatus(upload_ticket)

        # this is a workaround for a bug in vimeo API
        # sometimes, after a video is uploaded
        # changing meta data fails... there must be
        # some delays somewhere... so put failed tries
        # in a queue, that should be treated later
        try :
            self.videos_setTitle(vid, title)
            self.videos_setPrivacy(vid)

            if len(tags) > 0:
                self.videos_addTags(vid, tags)
        except CurlyRestException,e:
            print "Failed to change metadata for video ", vid
            print "queuing for later..."
            self.vimeo_bug_queue.append((vid, title, tags))
        
        print vid

    #
    # Follows the API implementation itself.
    #
    def auth_getFrob(self):
        m = "vimeo.auth.getFrob"
        (url, u) = self.get_url_sig({'api_key': self.apikey,
                                     'method' : m})
        url = BASE_URL + url
        t = self.curly.do_rest_call(url)

        frob = t.find("frob")

        if frob == None:
            raise VimeoException()

        self.frob = frob.text

        
    def auth_getToken(self):
        if self.frob == None:
            msg = "Missing frob for getting authentication ticket!"
            raise VimeoException(msg)

        m = "vimeo.auth.getToken"
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'frob' : self.frob,
                                       'method': m})
        url = BASE_URL + url
        t = self.curly.do_rest_call(url)

        self.auth_token = t.findtext("auth/token")
        print self.auth_token
        self.auth_perms = t.findtext("auth/perms")
        unode = t.find("auth/user")

        if None in (self.auth_token, self.auth_perms, unode):
            raise VimeoException("Could not get token for frob " + self.frob)

        self.user_dic = unode.attrib

    def videos_setPrivacy(self, video_id, privacy="anybody"):
        m = "vimeo.videos.setPrivacy"
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'video_id' : video_id,
                                       'user_id': self.user_id,
                                       'privacy': privacy,
                                       'method' : m})
        t = self.curly.do_rest_call(BASE_URL + url)


    def test_login(self):
        if self.auth_token == None:
            raise VimeoException("Missing authentication token!")

        m = "vimeo.test.login"
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'method' : m})
        url = BASE_URL + url
        t = self.curly.do_rest_call(url)
        un = t.find("user/username")

        if un == None:
            raise VimeoException("Invalid response from server !")

        uid = t.find("user").attrib['id']

        print "Username: %s [%s]" % (un.text, uid)

    def videos_setTitle(self, video_id, title):
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'video_id' : video_id,
                                       'user_id': self.user_id,
                                       'title' : title,
                                       'method' : 'vimeo.videos.setTitle'})

        t = self.curly.do_rest_call(BASE_URL + url)


    def videos_addTags(self, video_id, tags):
        print "tagging %s with %s" % (video_id, ",".join(tags))
        ntags = [urllib.quote_plus(tag) for tag in tags]

        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'video_id' : video_id,
                                       'user_id' : self.user_id,
                                       'tags' : ",".join(ntags),
                                       'method': 'vimeo.videos.addTags'})
        t = self.curly.do_rest_call(BASE_URL + url)

        
    def videos_getUploadTicket(self):
        if self.auth_token == None:
            raise VimeoException("Missing authentication token!")

        if self.user_id == None:
            raise VimeoException("Missing user_id, you have to " +
                                 "call set_userid() first!")

        m = "vimeo.videos.getUploadTicket"
        (url, sig) = self.get_url_sig({'api_key' : self.apikey,
                                       'auth_token': self.auth_token,
                                       'user_id': self.user_id,
                                       'method': m})

        t = self.curly.do_rest_call(BASE_URL + url)

        upload_ticket = t.find("ticket")
        
        if upload_ticket == None:
            print t.attrib
            print t.find('err').attrib
            raise VimeoException("Invalid response from server!")

        upload_ticket = upload_ticket.attrib['id']
        return upload_ticket
    
    def videos_checkUploadStatus(self, ticket):
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'ticket_id': ticket,
                                       'user_id': self.user_id,
                                       'method' : "vimeo.videos.checkUploadStatus"})
        url = BASE_URL + url
        t = self.curly.do_rest_call(url)

        upload_ticket = t.find("ticket")

        if upload_ticket == None or 'video_id' not in upload_ticket.attrib:
            raise VimeoException("Invalid response from server!")

        return upload_ticket.attrib['video_id']
        
    def upload(self, video_file, ticket):
        (url, sig) = self.get_url_sig({'api_key': self.apikey,
                                       'auth_token': self.auth_token,
                                       'ticket_id': ticket})

        res = self.curly.do_post_call("http://vimeo.com/services/upload",
                                      [("video", (pycurl.FORM_FILE, video_file)),
                                       ("api_key", self.apikey),
                                       ("auth_token", self.auth_token),
                                       ("ticket_id", ticket),
                                       ("api_sig", sig)], True)
        # the API does not provide any return value
        # for the POST.
    
    def test_echo(self, dic_args):
        pass
# vimeo.test.echo
# This will just repeat back any parameters that you send.
# Authentication
# Authentication is not required.
# Returns

# <foo>bar</foo>
# <some_string>Hi-Ya!</some_strong>

    def test_null(self):
        pass
# vimeo.test.null
# This is just a simple null/ping test...
# Authentication
# Authentication is required with 'read' permission.
# Returns
# This method returns an empty success response.

# <rsp stat="ok"></rsp>

    def auth_checkToken(self):
        (url,sig) = self.get_url_sig({'api_key': self.apikey,
                                      'auth_token': self.auth_token,
                                      'method': 'vimeo.auth.checkToken'})
        url = BASE_URL + url
        t = self.curly.do_rest_call(url)
        user_e = t.find('auth/user')
        user = {'id':user_e.attrib['id'],
                'username': user_e.attrib['username'],
                'fullname': user_e.attrib['fullname']}
        perms = t.find('auth/perms').text
        return (perms, user)

#     vimeo.auth.checkToken
# Checks the validity of the token. Returns the user associated with it.
# Returns the same as vimeo.auth.getToken
# Authentication
# Authentication is not required.
# Parameters

#     * string auth_token - - Just send the auth token

# Returns

# <auth>
#    <token>12354</token>
#    <perms>write</perms>
#    <user id="151542" username="ted" fullname="Ted!" />
# </auth>

# Error Codes

#     * 98: Login failed / Invalid auth token

    def videos_getList(self, userid, page, per_page):
        pass
# vimeo.videos.getList
# This gets a list of videos for the specified user.

# This is the functionality of "My Videos" or "Ted's Videos."

# At the moment, this is the same list as vimeo.videos.getAppearsInList. If you need uploaded or appears in, those are available too.
# Authentication
# Authentication is not required.
# Parameters

#     * string user_id - User ID, this can be the ID number (151542) or the username (ted)
#     * int page - Which page to show.
#     * int per_page - How many results per page?

# Returns
# The default response is this:

# <videos page="1" perpage="25" on_this_page="2">
# 	<video id="173727" owner="151542" title="At the beach" privacy="users" is_hd="0" />
# 	<video id="173726" owner="151542" title="The Kids" privacy="contacts" is_hd="0" />
# </videos>

# If you pass fullResponse=1 as a parameter, the video object is identical to the vimeo.videos.getInfo call. 

    def videos_getUploadList(self, user_id, page, per_page):
        pass
#     vimeo.videos.getUploadedList
# This gets a list of videos uploaded by the specified user.

# If the calling user is logged in, this will return information that calling user has access to (including private videos). If the calling user is not authenticated, this will only return public information, or a permission denied error if none is available.
# Authentication
# Authentication is not required.
# Parameters

#     * string user_id - User ID, this can be the ID number (151542) or the username (ted)
#     * int page - Which page to show.
#     * int per_page - How many results per page?

# Returns
# The default response is this:

# <videos page="1" perpage="25" on_this_page="2">
# 	<video id="173727" owner="151542" title="At the beach" privacy="users" is_hd="0" />
# 	<video id="173726" owner="151542" title="The Kids" privacy="contacts" is_hd="0" />
# </videos>

# If you pass fullResponse=1 as a parameter, the video object is identical to the vimeo.videos.getInfo call. 

    def videos_getAppearsInList(self, user_id, page, per_page):
        pass
# vimeo.videos.getAppearsInList
# This gets a list of videos that the specified user appears in.

# If the calling user is logged in, this will return information that calling user has access to (including private videos). If the calling user is not authenticated, this will only return public information, or a permission denied error if none is available.
# Authentication
# Authentication is not required.
# Parameters

#     * string user_id - User ID, this can be the ID number (151542) or the username (ted)
#     * int page - Which page to show.
#     * int per_page - How many results per page?

# Returns
# The default response is this:

# <videos page="1" perpage="25" on_this_page="2">
# 	<video id="173727" owner="151542" title="At the beach" privacy="users" is_hd="0" />
# 	<video id="173726" owner="151542" title="The Kids" privacy="contacts" is_hd="0" />
# </videos>

# If you pass fullResponse=1 as a parameter, the video object is identical to the vimeo.videos.getInfo call. 

    def videos_getSubscriptionsList(self, user_id, page, per_page):
        pass
 #    vimeo.videos.getSubscriptionsList
# This gets a list of subscribed videos for a particular user.

# If the calling user is logged in, this will return information that calling user has access to (including private videos). If the calling user is not authenticated, this will only return public information, or a permission denied error if none is available.
# Authentication
# Authentication is not required.
# Parameters

#     * string user_id - User ID, this can be the ID number (151542) or the username (ted) %user_default%
#     * int page - Which page to show.
#     * int per_page - How many results per page?

# Returns
# The default response is this:

# <videos page="1" perpage="25" on_this_page="2">
# 	<video id="173727" owner="151542" title="At the beach" privacy="users" is_hd="0" />
# 	<video id="173726" owner="151542" title="The Kids" privacy="contacts" is_hd="0" />
# </videos>

# If you pass fullResponse=1 as a parameter, the video object is identical to the vimeo.videos.getInfo call. 

    def videos_getListByTag(self, tag, user_id, page, per_page):
        pass
#     vimeo.videos.getListByTag
# This gets a list of videos by tag

# If you specify a user_id, we'll only get video uploaded by that user
# with the specified tag.

# If the calling user is logged in, this will return information that calling user has access to (including private videos). If the calling user is not authenticated, this will only return public information, or a permission denied error if none is available.
# Authentication
# Authentication is not required.
# Parameters

#     * string tag (required) - A single tag: "cat" "new york" "cheese"
#     * string user_id - User ID, this can be the ID number (151542) or the username (ted) %user_default%
#     * int page - Which page to show.
#     * int per_page - How many results per page?

# Returns
# The default response is this:

# <videos page="1" perpage="25" on_this_page="2">
# 	<video id="173727" owner="151542" title="At the beach" privacy="users" is_hd="0" />
# 	<video id="173726" owner="151542" title="The Kids" privacy="contacts" is_hd="0" />
# </videos>

# If you pass fullResponse=1 as a parameter, the video object is identical to the vimeo.videos.getInfo call. 
