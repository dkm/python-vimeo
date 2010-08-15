#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#   Python module for Vimeo
#   Copyright (C) 2009  Marc Poulhiès
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


from distutils.core import setup

setup (
    name = "vimeo",
    description = "Python module for vimeo",
    long_description = """
Python module for using API offered by vimeo
""",
    version = "0.2",
    author = 'Marc Poulhiès',
    author_email = 'dkm@kataplop.net',
    url = "http://github.com/dkm/python-vimeo",
    maintainer = 'Marc Poulhiès',
    maintainer_email = 'dkm@kataplop.net',
    license = "GPL,MIT",
    packages = ['vimeo'],
    scripts=['bin/vimeo-uploadv2.py', 'bin/vimeo-query.py'],
    )

