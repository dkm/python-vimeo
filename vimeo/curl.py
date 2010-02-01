#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2009 Marc Poulhiès
#
# Python module for Vimeo
# originaly part of 'plopifier'
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


import pycurl
import xml.etree.ElementTree as ET

USER_AGENT = 'python-vimeo http://github.com/dkm/python-vimeo'
TURNING_BAR='|/-\\'

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
    """
    A CurlyRequest object is used to send HTTP requests.
    It's a simple wrapper around basic curl methods.
    In particular, it can upload files and display a progress bar.
    """
    def __init__(self, pbarsize=19):
        self.buf = None
        self.pbar_size = pbarsize
        self.pidx = 0

    def do_rest_call(self, url):
        """
        Send a simple GET request and interpret the answer as a REST reply.
        """

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

    def _body_callback(self, buf):
        self.buf += buf
        return len(buf)

    def do_request(self, url):
        """
        Send a simple GET request
        """

        self.buf = ""
        curl = pycurl.Curl()
        curl.setopt(pycurl.USERAGENT, USER_AGENT)
        curl.setopt(curl.URL, url)
        curl.setopt(curl.WRITEFUNCTION, self._body_callback)
        curl.perform()
        curl.close()
        p = self.buf
        self.buf = ""
        return p
    
    def _upload_progress(self, download_t, download_d, upload_t, upload_d):
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
        """
        Send a simple POST request
        """
        c = pycurl.Curl()
        c.setopt(c.POST, 1)
        c.setopt(c.URL, url)
        c.setopt(c.HTTPPOST, args)
        c.setopt(c.WRITEFUNCTION, self._body_callback)
        #c.setopt(c.VERBOSE, 1)
        self.buf = ""

        c.setopt(c.NOPROGRESS, 0)
        
        if use_progress:
            c.setopt(c.PROGRESSFUNCTION, self._upload_progress)

        c.perform()
        c.close()
        res = self.buf
        self.buf = ""
        return res
