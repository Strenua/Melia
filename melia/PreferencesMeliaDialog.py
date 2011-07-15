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

# This is your preferences dialog.
#
# Define your preferences dictionary in the __init__.main() function.
# The widget names in the PreferencesTestProjectDialog.ui
# file need to correspond to the keys in the preferences dictionary.
#
# Each preference also need to be defined in the 'widget_methods' map below
# to show up in the dialog itself.  Provide three bits of information:
#  1) The first entry is the method on the widget that grabs a value from the
#     widget.
#  2) The second entry is the method on the widget that sets the widgets value
#      from a stored preference.
#  3) The third entry is a signal the widget will send when the contents have
#     been changed by the user. The preferences dictionary is always up to
# date and will signal the rest of the application about these changes.
# The values will be saved to desktopcouch when the application closes.
#
# TODO: replace widget_methods with your own values

import gtk, gobject

widget_methods = {
    'orientation': ['get_active', 'set_active', 'changed', 'set_orientation'], # Added another column here for the method (of the MeliaWindow) to be called for live updates
    'launcher_height': ['get_value', 'set_value', 'value-changed', 'update_height'],
    'launcher_width': ['get_value', 'set_value', 'value-changed', 'update_width'],
    'button_style': ['get_active', 'set_active', 'changed', 'update_button_style'],
    'panel_transparent': ['get_active', 'set_active', 'toggled', 'set_transparent'],
    'desktop_dash': ['get_active', 'set_active', 'toggled', 'show_deskdash'],
}

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import logging
logger = logging.getLogger('melia')

from melia_lib.PreferencesDialog import PreferencesDialog
from melia_lib.preferences import preferences

class PreferencesMeliaDialog(PreferencesDialog):
    __gtype_name__ = "PreferencesMeliaDialog"

    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the preferences dialog"""
        super(PreferencesMeliaDialog, self).finish_initializing(builder)

        preferences.db_connect()
        preferences.load()

        # populate the dialog from the preferences dictionary
        # using the methods from widget_methods
        self.widget_methods = widget_methods
        self.set_widgets_from_preferences() # pylint: disable=E1101

        # Code for other initialization actions should be added here.
        
        # set up the combobox objects
        self.ui.liststore1.append(('vertical',))
        self.ui.liststore1.append(('horizontal',))
        self.ui.orientation.set_model(self.ui.liststore1)
        self.ui.orientation.show_all()
        
        self.ui.liststore2.append(('new',))
        self.ui.liststore2.append(('old',))
        self.ui.button_style.set_model(self.ui.liststore2)
        self.ui.button_style.show_all()
        
        for i in preferences['indicators']:
            #self.ui.liststore3.append(('hello',))
            ''
        self.ui.treeview1.set_model(self.ui.liststore3)
        
        
        