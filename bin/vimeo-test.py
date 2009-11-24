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

from vimeo import SimpleOAuthClient
import vimeo
import oauth.oauth as oauth
import sys
import optparse

def main(argv):
    parser = optparse.OptionParser(
        usage='Usage: %prog [options]',
        description="Simple Vimeo uploader")
    parser.add_option('-k', '--key',
                      help="Auth key")
    parser.add_option('-s', '--secret',
                      help="Auth secret")

    (options, args) = parser.parse_args(argv[1:])
    
    if None in (options.key, options.secret):
        print "Missing key or secret"
        sys.exit(-1)
    
    client = SimpleOAuthClient(options.key, options.secret)
    client.get_request_token()
    print client.get_authorize_token_url()
    verifier = sys.stdin.readline().strip()
    print "Using ", verifier, " as verifier"
    print client.get_access_token(verifier)

    client.vimeo_videos_upload_getQuota()
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


