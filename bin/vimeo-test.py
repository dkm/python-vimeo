#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
#
# python-vimeo is free software: you can redistribute it and/or modify
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
This script contains various call to vimeo API
in order the check the correct behavior of python-vimeo.
"""

from vimeo import SimpleOAuthClient
import vimeo
import oauth.oauth as oauth
import sys
import optparse


def test_albums(client):
    video_ids = [xxx,yyy,zzz]
    user_id = uid

    client.vimeo_albums_addVideo(self, album_id, video_id)

    a1 = client.vimeo_albums_create(title, video_id)
    a2 = client.vimeo_albums_create(title, video_id, description=None)
    a3 = client.vimeo_albums_create(title, video_id, videos=videos_ids)
    
    client.vimeo_albums_delete(a2)
    client.vimeo_albums_delete(a3)

    client.vimeo_albums_getAll(uid)
    client.vimeo_albums_getAll(uid, sort="newest")
    client.vimeo_albums_getAll(uid, sort="oldest")
    client.vimeo_albums_getAll(uid, sort="alphabetical")

    client.vimeo_albums_getAll(uid, sort="newest", page=2)
    client.vimeo_albums_getAll(uid, sort="oldest", page=2)
    client.vimeo_albums_getAll(uid, sort="alphabetical", page=2)

    client.vimeo_albums_getAll(uid, sort="newest", per_page=35)
    client.vimeo_albums_getAll(uid, sort="oldest", per_page=35)
    client.vimeo_albums_getAll(uid, sort="alphabetical", per_page=35)

    client.vimeo_albums_getVideos(a1, full_response=None)
    client.vimeo_albums_getVideos(a1, full_response=True)

    client.vimeo_albums_removeVideo(a1)
    client.vimeo_albums_removeVideo(a1, video_ids[0])

    client.vimeo_albums_setDescription(a1, "toto toto")
    client.vimeo_albums_setPassword(a1, "abcd")
    client.vimeo_albums_setTitle(a1, "toto title")

def test_videos(client):
    user_ids=[xxx, yyy, zzz]
    video_ids=[xxx, yyy, zzz]
    client.vimeo_videos_addCast(user_ids[0], video_ids[0])

    client.vimeo_videos_addPhotos(photos_urls, video_id)
    client.vimeo_videos_addTags(tags, video_id)
    client.vimeo_videos_clearTags(video_id)
    client.vimeo_videos_delete(video_id)
    client.vimeo_videos_getAll(user_id,)
    client.vimeo_videos_getAppearsIn(user_id,)
    client.vimeo_videos_getByTag(tag, )
    client.vimeo_videos_getCast(video_id,)
    client.vimeo_videos_getContactsLiked(user_id,)
    client.vimeo_videos_getContactsUploaded(user_id, )
    client.vimeo_videos_getInfo(video_id)
    client.vimeo_videos_getLikes(user_id,)
    client.vimeo_videos_getSourceFileUrls(video_id)
    client.vimeo_videos_getSubscriptions(user_id,
    client.vimeo_videos_getThumbnailUrls(video_id)
    client.vimeo_videos_getUploaded(user_id,)
    client.vimeo_videos_removeCast(user_id, video_id)
    client.vimeo_videos_removeTag(tag_id, video_id)
    client.vimeo_videos_search(query, user_id=None,)
    client.vimeo_videos_setDescription(description, video_id)
    client.vimeo_videos_setLike(like, video_id)
    client.vimeo_videos_setPrivacy(privacy, video_id,)
    client.vimeo_videos_setTitle(title, video_id)
    client.vimeo_videos_comments_addComment(comment_text, video_id,)
    client.vimeo_videos_comments_deleteComment(comment_id, video_id)
    client.vimeo_videos_comments_editComment(comment_id,)
    client.vimeo_videos_comments_getList(video_id,)
    client.vimeo_videos_embed_getPresets(page=None, per_page=None)
    client.vimeo_videos_embed_setPreset(preset_id,)


def test_upload(client):
                                             
#     client.vimeo_videos_upload_checkTicket(ticket_id)
#     client.vimeo_videos_upload_confirm(ticket_id,
#     client.vimeo_videos_upload_getTicket(self)
#     client.vimeo_videos_upload_verifyManifest(json_manifest, ticket_id, xml_manifest)



def main(argv):
    parser = optparse.OptionParser(
        usage='Usage: %prog [options]',
        description="Simple Vimeo uploader")
    parser.add_option('-k', '--key',
                      help="Consumer key")
    parser.add_option('-s', '--secret',
                      help="Consumer secret")
    parser.add_option('-t', '--access-token',
                      help="Access token")
    parser.add_option('-y', '--access-token-secret',
                      help="Access token secret")


    (options, args) = parser.parse_args(argv[1:])
    
    if None in (options.key, options.secret):
        print "Missing key or secret"
        sys.exit(-1)

    if None in (options.access_token, options.access_token_secret):
        client = SimpleOAuthClient(options.key, options.secret)
        client.get_request_token()
        print client.get_authorize_token_url()
        verifier = sys.stdin.readline().strip()
        print "Using ", verifier, " as verifier"
        print client.get_access_token(verifier)
    else:
        client = SimpleOAuthClient(options.key, options.secret,
                                   token=options.access_token,
                                   token_secret=options.access_token_secret)

#     print "getQuota"
#     client.vimeo_videos_upload_getQuota()

#     # print "test null"
#     # client.vimeo_test_null()
    
#     # print "test login"
#     # client.vimeo_test_login()

#     print "test echo"
#     client.vimeo_test_echo({'tata':'prout', 'prout':'caca'})

#     print "albums getAll"
#     client.vimeo_albums_getAll('1443699')
    
#     print "channels getAll"
#     client.vimeo_channels_getAll()

    # oauth_request = oauth.OAuthRequest.from_token_and_callback(token=token, 
    #                                                            http_url=client.authorization_url)
    # response = client.authorize_token(oauth_request)
    # print response

    # oauth_request = oauth.OAuthRequest.from_consumer_and_token(consumer, 
    #                                                            token=token, 
    #                                                            http_method='GET', 
    #                                                            http_url=RESOURCE_URL, 
    #                                                            parameters=parameters)
    # oauth_request.sign_request(signature_method_hmac_sha1, consumer, token)

if __name__ == '__main__':
    main(sys.argv)
    ##print vimeo.user_videos('dkm')


