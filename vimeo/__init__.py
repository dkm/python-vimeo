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

# this is stupid, use python-oauth instead!
# import hmac
# import hashlib
# import base64

# ## do not move the '%' from the begining!
# percent_encode = {
#     '%' : "%25",
#     '!' : "%21",
#     '*' : "%2A",
#     "'" : "%27",
#     '(' : "%28", 
#     ')' : "%29", 
#     ';' : "%3B",
#     ':' : "%3A",
#     '@' : "%40",
#     '&' : "%26",
#     '=' : "%3D",
#     '+' : "%2B",
#     '$' : "%24",
#     ',' : "%2C",
#     '/' : "%2F",
#     '?' : "%3F",
#     '#' : "%23",
#     '[' : "%5B",
#     ']' : "%5D",
# }

# def percent_encode_str(str_to_enc):
#     for k,v in percent_encode.items():
#         str_to_enc = str_to_enc.replace(k,v)
#     return str_to_enc

# def gen_sig(str_to_sign, key):
#     hm = hmac.new(key, digest=hashlib.sha1())
#     hm.update(str_to_sign)
#     return base64.b64encode(hm.digest())
