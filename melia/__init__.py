# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# Copyright (C) 2011 <Michael Smith> <crazedpsyc@lavabit.com>
# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License version 3, as published 
# by the Free Software Foundation.
# 
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranties of 
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
# PURPOSE.  See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along 
# with this program.  If not, see <http://www.gnu.org/licenses/>.
### END LICENSE

import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import gtk

from melia import MeliaWindow, MeliaPanelDialog

from melia_lib import set_up_logging, preferences, get_version, melia_dbus

def parse_options():
    """Support for command line options"""
    parser = optparse.OptionParser(version="%%prog %s" % get_version())
    parser.add_option(
        "-v", "--verbose", action="count", dest="verbose",
        help=_("Show debug messages (-vv debugs melia_lib also)"))

    (options, args) = parser.parse_args()

    set_up_logging(options)

def main():
    'constructor for your class instances'
    parse_options()


    # Run the application. 
    #gtk.timeout_add(100, melia_dbus.run())   
    window = MeliaWindow.MeliaWindow()
    window.show()

    melia_dbus.init(window)
    #melia_dbus.run()

    gtk.main()
    
    preferences.save()
