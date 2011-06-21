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
    'launcher_width': 48.0,
    'launcher_height': 'default',
    'button_style': 0, # 0 = new, 1 = old
    'panel_transparent': False,
    'dash_button_font_color': '#000',
    'desktop_dash': True,
    'custom_colors': True, # use custom (non-themey) colors for the panel/launcher?
    'autohide_launcher': False,
    }
    preferences.update(default_preferences)
    # user's stored preferences are used for 2nd and subsequent sessions
    preferences.db_connect()
    preferences.load()
    preferences.update(default_preferences)
    preferences.save()

    # Run the application.    
    window = MeliaWindow.MeliaWindow()
    window.show()
    
    # THIS THING IS B0RK3D!!!! (FIXME)    
    #panel = MeliaPanelDialog.MeliaPanelDialog()
    #panel.show()
    gtk.main()
    
    preferences.save()
