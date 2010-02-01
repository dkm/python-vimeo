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
    parser.add_option('--get-channel-info', metavar="CHAN_ID",
                      help="Get info on a specific channel")
    parser.add_option('--get-video-info', metavar="VID_ID",
                      help="Get info on a specific video")
    parser.add_option('--page', metavar="NUM",
                      help="Page number, when it makes sense...")
    parser.add_option('--per-page', metavar="NUM",
                      help="Per page number, when it makes sense...")
    parser.add_option('--sort', metavar="SORT",
                      help="sort order, when it makes sense (accepted values depends on the query)...")
    parser.add_option('--get-channel-moderators', metavar="CHAN_ID",
                      help="Get moderators for a specific channel")
    parser.add_option('--get-channel-subscribers', metavar='CHAN_ID',
                      help="Get subscribers for a specific channel")
    parser.add_option('--get-channel-videos', metavar='CHAN_ID',
                      help="Get videos for a specific channel")
    parser.add_option('--get-contacts', metavar='USER_ID',
                      help="Get all contacts for a specific user")

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

    elif options.get_channels:
        channels = client.vimeo_channels_getAll(page=options.page,
                                                per_page=options.per_page)
        for channel in channels.findall("channels/channel"):
            print "Name (%s):" %channel.attrib['id'], channel.find('name').text
    
    elif options.get_channel_info != None:
        info = client.vimeo_channels_getInfo(options.get_channel_info).find('channel')
        for text_item in ['name', 'description', 'created_on', 'modified_on', 'total_videos',
                          'total_subscribers', 'logo_url', 'badge_url', 'url', 'featured_description']:
                          
            it = info.find(text_item)
            if it != None:
                print "%s:" %text_item, info.find(text_item).text
        creator = info.find('creator')
        print "Creator: %s (%s)" %(creator.attrib['display_name'], creator.attrib['id'])
       
    elif options.get_video_info != None:
        info = client.vimeo_videos_getInfo(options.get_video_info)
        ET.dump(info)
    
    elif options.get_channel_moderators != None:
        moderators = client.vimeo_channels_getModerators(options.get_channel_moderators,
                                                         page=options.page,
                                                         per_page=options.per_page)
        for moderator in moderators.findall('moderators/user'):
            print "Name: %s (%s)" %(moderator.attrib['display_name'], moderator.attrib['id'])

    elif options.get_channel_subscribers != None:
        subs = client.vimeo_channels_getSubscribers(options.get_channel_subscribers,
                                                    page=options.page,
                                                    per_page=options.per_page)
        for sub in subs.findall('subscribers/subscriber'):
            print "Name: %s (%s)" %(sub.attrib['display_name'], sub.attrib['id'])

    elif options.get_channel_videos != None:
        vids = client.vimeo_channels_getVideos(options.get_channel_videos,
                                               page=options.page,
                                               per_page=options.per_page)
        for vid in vids.findall('videos/video'):
            print "Video: %s (%s), uploaded %s" %(vid.attrib['title'], 
                                                  vid.attrib['id'], 
                                                  vid.attrib['upload_date'])
    elif options.get_contacts:
        contacts = client.vimeo_contacts_getAll(options.get_contacts,
                                                sort=options.sort,
                                                page=options.page,
                                                per_page=options.per_page)
        for contact in contacts.findall('contacts/contact'):
            print "Contact: %s (%s)" %(contact.attrib['display_name'], contact.attrib['id'])
                                                
if __name__ == '__main__':
    main(sys.argv)


