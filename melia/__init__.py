# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import gtk

from melia import MeliaWindow, MeliaPanelDialog

from melia_lib import set_up_logging, preferences, get_version

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

    # preferences
    # set some values for our first session
    default_preferences = {
    'example_entry': 'I remember stuff',
    'orientation': 0, # 0=vertical 1=horizontal
    'top_panel_height': 25,
    'launcher_x_pos': 0,
    'launcher_y_pos': 25,
    'launcher_width': 48,
    'launcher_height': 'default',
    'button_style': 'new',
    }
    preferences.update(default_preferences)
    # user's stored preferences are used for 2nd and subsequent sessions
    preferences.db_connect()
    preferences.load()

    # Run the application.    
    window = MeliaWindow.MeliaWindow()
    window.show()
    
    # THIS THING IS B0RK3D!!!! (FIXME)    
    #panel = MeliaPanelDialog.MeliaPanelDialog()
    #panel.show()
    gtk.main()
    
    preferences.save()
