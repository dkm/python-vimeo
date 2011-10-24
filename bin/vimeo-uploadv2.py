#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This is distributed in the hope that it will be useful,
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
import vimeo.convenience

import sys,time
import optparse

## use a sleep to wait a few secs for vimeo servers to be synced.
## sometimes, going too fast
sleep_workaround = True

def main(argv):
    parser = optparse.OptionParser(
        usage='Usage: %prog [options]',
        description="Simple Vimeo uploader")

    # auth/appli stuff
    parser.add_option('-k', '--key',
                      help="Consumer key")
    parser.add_option('-s', '--secret',
                      help="Consumer secret")
    parser.add_option('-t', '--access-token',
                      help="Access token")
    parser.add_option('-y', '--access-token-secret',
                      help="Access token secret")
    # file upload stuff
    parser.add_option('-f', '--file',
                      help="Video file to upload")
    parser.add_option('--title',
                      help="Set the video title")
    parser.add_option('--description',
                      help="Set the video description")
    parser.add_option('--privacy',
                      help="Set the video privacy (anybody; nobody; contacts; users:u1,u2; password:pwd; disable)")

    (options, args) = parser.parse_args(argv[1:])

    vconfig = vimeo.config.VimeoConfig(options)

    if not vconfig.has_option("appli", "consumer_key"):
        print "Missing consumer key"
        parser.print_help()
        sys.exit(-1)

    if not vconfig.has_option("appli", "consumer_secret"):
        print "Missing consumer secret"
        parser.print_help()
        sys.exit(-1)

    if options.file == None:
        print "Missing file to upload!"
        parser.print_help()
        sys.exit(-1)

    if not (vconfig.has_option("auth", "token") and vconfig.has_option("auth", "token_secret")):
        client = vimeo.VimeoClient(key=vconfig.get("appli", "consumer_key"),
                                   secret=vconfig.get("appli", "consumer_secret"))
        client.get_request_token()
        print client.get_authorization_url(permission="write")
        verifier = sys.stdin.readline().strip()
        print "Using", verifier, "as verifier"
        print client.get_access_token(verifier)
    else:
        client = vimeo.VimeoClient(key=vconfig.get("appli", "consumer_key"),
                                   secret=vconfig.get("appli", "consumer_secret"),
                                   token=vconfig.get("auth","token"),
                                   token_secret=vconfig.get("auth", "token_secret"),
                                   format="json")

    quota = client.vimeo_videos_upload_getQuota()
    print "Your current quota is", int(quota['upload_space']['free'])/(1024*1024), "MiB"
    
    t = client.vimeo_videos_upload_getTicket()
    vup = vimeo.convenience.VimeoUploader(client, t, quota=quota)
    vup.upload(options.file)
    vid = vup.complete()['video_id']
    print vid
    # do we need to wait a bit for vimeo servers ?
    if sleep_workaround and (options.title != None or options.description != None):
        time.sleep(5)        

    if options.title != None:
        client.vimeo_videos_setTitle(options.title, vid)
    if options.description != None:
        client.vimeo_videos_setDescription(options.description, vid)

    if options.privacy != None:
        pusers = []
        ppwd = None
        ppriv = options.privacy
        if options.privacy.startswith("users"):
            pusers = options.privacy.split(":")[1].split(',')
            ppriv = "users"
        if options.privacy.startswith("password"):
            ppwd = options.privacy.split(":")[1]
            ppriv = "password"

        client.vimeo_videos_setPrivacy(ppriv, vid, 
                                       users=pusers, password=ppwd)
        
if __name__ == '__main__':
    main(sys.argv)


