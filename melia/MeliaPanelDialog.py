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

import os
import gtk
import cairo

from melia_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import logging
logger = logging.getLogger('melia')

from melia_lib.preferences import preferences

def set_indicator_menu_pos(menu, data=None):
    print menu, data
    return (1290, 25, True)


def transparent_expose(widget, event):
	cr = widget.window.cairo_create()
	cr.set_operator(cairo.OPERATOR_CLEAR)
	region = gtk.gdk.region_rectangle(event.area)
	cr.region(region)
	cr.fill()
	return False
	
def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    
	
class MeliaPanelDialog(gtk.Window):
    __gtype_name__ = "MeliaPanelDialog"

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated MeliaPanelDialog object.
        """
        builder = get_builder('MeliaPanelDialog')
        new_object = builder.get_object('melia_panel_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a MeliaPanelDialog object with it in order to
        finish initializing the start of the new MeliaPanelDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        
       
        preferences.db_connect()
        preferences.load()

        if preferences['panel_transparent']:
            #self.widgefy(self)
            self.widgefy(self.ui.melia_panel_dialog)
            self.widgefy(self.ui.hbox1)
            self.widgefy(self.ui.hbox3)
            self.widgefy(self.ui.hbox4)
            self.widgefy(self.ui.dashbutton)
            self.widgefy(self.ui.layout3)
            self.widgefy(self.ui.layout4)
            self.widgefy(self.ui.layout1)
            self.widgefy(self.ui.hbox2)
            self.widgefy(self.ui.indicator_panel)
            self.widgefy(self.ui.layout8)
            self.widgefy(self.ui.layout7)
            self.widgefy(self.ui.notification_box)
            self.widgefy(self.ui.notification_area)
            self.widgefy(self.ui.layout2)
        
        self.left_button = None 
        self.active_indicator = None  
        self.indicators = [] 
        
        ## SET UP THE NOTIFICATION AREA
        self.ui.notification_mi = gtk.ImageMenuItem()
        self.ui.notification_area.append(self.ui.notification_mi)
        self.ui.notification_area.show_all()
        
        ##

        for indicator in preferences['indicators']:
            #try:
                i = my_import('indicators.' + indicator)
                if hasattr(i, 'menu'): 
                    menu = i.menu()
                    self.ui.indicator_panel.add(menu)
                    print menu
                    #self.ui.indicator_panel.add(btn)
                    self.indicators.append(menu)
                else: logger.warn('Indicator %s does not appear to have a menu' % indicator)
            #except: logger.warn('Failed to load indicator: %s' % indicator)
            
        
        self.ui.indicator_panel.show_all()
        self.move(0, 0)
        
        
    def widgefy(self, widget):
        screen = widget.get_screen()
        rgba = screen.get_rgba_colormap()
        widget.set_colormap(rgba)
        widget.set_app_paintable(True)
        widget.connect("expose-event", transparent_expose)


if __name__ == "__main__":
    dialog = MeliaPanelDialog()
    dialog.show()
    gtk.main()
