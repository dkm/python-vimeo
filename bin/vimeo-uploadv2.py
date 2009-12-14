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


import vimeo
import oauth.oauth as oauth
import sys
import optparse


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
    parser.add_option('-v', '--verifier',
                      help="Verifier for token")


    (options, args) = parser.parse_args(argv[1:])
    
    if None in (options.key, options.secret):
        print "Missing key or secret"
        sys.exit(-1)

    if None in (options.access_token, options.access_token_secret, options.verifier):
        client = vimeo.VimeoOAuthClient(options.key, options.secret)
        client.get_request_token()
        print client.get_authorize_token_url(permission="write")
        verifier = sys.stdin.readline().strip()
        print "Using", verifier, "as verifier"
        print client.get_access_token(verifier)
    else:
        client = vimeo.VimeoOAuthClient(options.key, options.secret,
                                        token=options.access_token,
                                        token_secret=options.access_token_secret,
                                        verifier=options.verifier)


    quota = client.vimeo_videos_upload_getQuota().find('user/upload_space').attrib['free']
    print "Your current quota is", int(quota)/(1024*1024), "MiB"
    
    t = client.vimeo_videos_upload_getTicket().find('ticket')
    (tid, endp) = (t.attrib['id'], t.attrib['endpoint'])
    print tid, endp
    print client._do_compute_vimeo_upload(endp, tid)
    
    

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


