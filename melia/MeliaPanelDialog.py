# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import os
import gtk
import cairo

from melia_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

from melia_lib.preferences import preferences
preferences.db_connect()
preferences.load()

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
        
        self.ui.indicator_system.connect('toggled', self.indicator_system_toggled)
        
        if preferences['panel_transparent']:
            screen = self.get_screen()
            rgba = screen.get_rgba_colormap()
            self.set_colormap(rgba)
            self.set_app_paintable(True)
            self.connect("expose-event", transparent_expose)

    def on_btn_ok_clicked(self, widget, data=None):
        """The user has elected to save the changes.

        Called before the dialog returns gtk.RESONSE_OK from run().
        """
        pass

    def on_btn_cancel_clicked(self, widget, data=None):
        """The user has elected cancel changes.

        Called before the dialog returns gtk.RESPONSE_CANCEL for run()
        """
        pass
        
    def indicator_system_toggled(self, widget, data=None):
        widget.set_size_request(0, 0)

        if self.ui.indicator_system_menu.get_children(): 
            self.ui.indicator_system_menu.popup(None, None, set_indicator_menu_pos, 0, gtk.get_current_event_time())
            return
        
        item = gtk.MenuItem('Lock Screen')
        #item.connect('activate', self.quicklaunch)
        self.ui.indicator_system_menu.append(item)
        self.ui.indicator_system_menu.append(gtk.SeparatorMenuItem())
        item = gtk.MenuItem('Guest Session')
        #item.connect('activate', self.quicklaunch)
        self.ui.indicator_system_menu.append(item)
        item = gtk.MenuItem('Switch From %s...' % os.getenv('LOGNAME'))
        #item.connect('activate', self.quicklaunch)
        self.ui.indicator_system_menu.append(item)
        self.ui.indicator_system_menu.show_all()
        self.ui.indicator_system_menu.popup(None, None, set_indicator_menu_pos, 0, gtk.get_current_event_time())
        self.ui.indicator_system_menu.button = widget
        self.ui.indicator_system_menu.connect('deactivate', self.indicator_untoggle)
        print widget.get_pointer()
        
    def indicator_untoggle(self, widget, data=None): 
        widget.button.set_state(gtk.STATE_NORMAL)
        
        
    def load_indicator(self, indicator):
        print indicator


if __name__ == "__main__":
    dialog = MeliaPanelDialog()
    dialog.show()
    gtk.main()
