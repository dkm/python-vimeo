#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
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
This script can be used to upload a video to Vimeo
It is using the 'advanced API', which is in the process
of being obsoleted by the API v2.
"""

import sys
import os
import optparse
import time
import vimeo

def main(argv):
    parser = optparse.OptionParser(
        usage='Usage: %prog [options]',
        description="Simple Vimeo uploader")

    # video_file = api_key = api_secret = authtok = title = None
    # tags=""

    parser.add_option('-f', '--video-file',
                      help="Video file to upload", metavar="video-file")
    parser.add_option('-k', '--vimeo-apikey', metavar='api-key',
                      help='set the "api_key" for vimeo')
    parser.add_option('-s', '--vimeo-secret', metavar='api-secret',
                      help='set the "secret" for vimeo')
    parser.add_option('-t', '--vimeo-authtoken', metavar='authtok',
                      help='set the "auth_token" for vimeo')
    parser.add_option('-n', '--video-title', metavar='title',
                      help='set the video title')
    parser.add_option('-g', '--video-tags', metavar='tags',
                      default="",
                      help='set the video tags as a coma separated list')

    (options, args) = parser.parse_args(argv[1:])

    if not options.video_file:
        parser.error("Missing video-file argument")

    if not (options.vimeo_apikey and options.vimeo_secret and options.vimeo_authtoken):
        parser.error("Missing vimeo credentials")

    v = vimeo.Vimeo(options.vimeo_apikey,
                    options.vimeo_secret,
                    options.vimeo_authtoken)
    v.set_userid()
    v.do_upload(options.video_file, options.video_title,
                tags=options.video_tags.split(','))

    while len(v.vimeo_bug_queue) > 0:
        v.process_bug_queue()
        time.sleep(1)

if __name__ == '__main__':
    main(sys.argv)
