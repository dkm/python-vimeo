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
This is an upload script for Vimeo using its v2 API
"""


import vimeo
import vimeo.config
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

    vconfig = vimeo.config.VimeoConfig(options)

    if not vconfig.has_option("appli", "consumer_key"):
        print "Missing consumer key"
        sys.exit(-1)

    if not vconfig.has_option("appli", "consumer_secret"):
        print "Missing consumer secret"
        sys.exit(-1)

    if not (vconfig.has_option("auth", "token") and vconfig.has_option("auth", "token_secret") and vconfig.has_option("auth", "verifier")):
        client = vimeo.VimeoOAuthClient(vconfig.get("appli", "consumer_key"),
                                        vconfig.get("appli", "consumer_secret"))
        client.get_request_token()
        print client.get_authorize_token_url(permission="write")
        verifier = sys.stdin.readline().strip()
        print "Using", verifier, "as verifier"
        print client.get_access_token(verifier)
    else:
        client = vimeo.VimeoOAuthClient(vconfig.get("appli", "consumer_key"),
                                        vconfig.get("appli", "consumer_secret"),
                                        token=vconfig.get("auth","token"),
                                        token_secret=vconfig.get("auth", "token_secret"),
                                        verifier=vconfig.get("auth", "verifier"))


    quota = client.vimeo_videos_upload_getQuota().find('user/upload_space').attrib['free']
    print "Your current quota is", int(quota)/(1024*1024), "MiB"
    
    t = client.vimeo_videos_upload_getTicket().find('ticket')
    (tid, endp) = (t.attrib['id'], t.attrib['endpoint'])
    print tid, endp
    print client._do_compute_vimeo_upload(endp, tid)
    
if __name__ == '__main__':
    main(sys.argv)
    ##print vimeo.user_videos('dkm')


