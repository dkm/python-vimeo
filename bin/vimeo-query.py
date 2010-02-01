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
import sys
import optparse
import xml.etree.ElementTree as ET

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
    parser.add_option('-v', '--verifier',
                      help="Verifier for token")
    parser.add_option('--quota',
                      help="Get user quota", action="store_true", default=False)
    parser.add_option('--get-channels',
                      help="Get all public channels", action="store_true", default=False)
    parser.add_option('--get-channel-info',
                      help="Get info on a specific channel")
    parser.add_option('--get-video-info',
                      help="Get info on a specific video")

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

    client = vimeo.VimeoOAuthClient(vconfig.get("appli", "consumer_key"),
                                    vconfig.get("appli", "consumer_secret"),
                                    token=vconfig.get("auth","token"),
                                    token_secret=vconfig.get("auth", "token_secret"),
                                    verifier=vconfig.get("auth", "verifier"))

    if options.quota:
        quota = client.vimeo_videos_upload_getQuota().find('user/upload_space').attrib['free']
        print "Your current quota is", int(quota)/(1024*1024), "MiB"
        sys.exit(0)

    if options.get_channels:
        channels = client.vimeo_channels_getAll()
        for channel in channels.findall("channels/channel"):
            print "Name (%s):" %channel.attrib['id'], channel.find('name').text
        sys.exit(0)
    
    if options.get_channel_info != None:
        info = client.vimeo_channels_getInfo(options.get_channel_info).find('channel')
        for text_item in ['name', 'description', 'created_on', 'modified_on', 'total_videos',
                          'total_subscribers', 'logo_url', 'badge_url', 'url', 'featured_description']:
                          
            it = info.find(text_item)
            if it != None:
                print "%s:" %text_item, info.find(text_item).text
        creator = info.find('creator')
        print "Creator: %s (%s)" %(creator.attrib['display_name'], creator.attrib['id'])
        sys.exit(0)
    
    if options.get_video_info != None:
        info = client.vimeo_videos_getInfo(options.get_video_info)
        ET.dump(info)
        sys.exit(0)
    
if __name__ == '__main__':
    main(sys.argv)


