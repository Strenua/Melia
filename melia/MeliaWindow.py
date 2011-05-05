# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE
import os
import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import gtk, wnck

screen = wnck.screen_get_default()
while gtk.events_pending():
    gtk.main_iteration()


def getwins():
    wins = screen.get_windows()
    return wins
    
import logging
logger = logging.getLogger('melia')

from melia_lib import Window
from melia.AboutMeliaDialog import AboutMeliaDialog
from melia.PreferencesMeliaDialog import PreferencesMeliaDialog

# See melia_lib.Window.py for more details about how this class works
class MeliaWindow(Window):
    __gtype_name__ = "MeliaWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MeliaWindow, self).finish_initializing(builder)

        #self.AboutDialog = AboutMeliaDialog
        #self.PreferencesDialog = PreferencesMeliaDialog

        # Code for other initialization actions should be added here.
        #color = gtk.gdk.color_parse('#000')
        #self.modify_bg(gtk.STATE_NORMAL, color)  
        #self.ui.layout1.modify_bg(gtk.STATE_NORMAL, color)        
        
        self.ui.Home.command = 'nautilus %s'
        home = os.getenv('HOME')
        self.ui.Home.list = {'Home': home, 'Documents': home + '/Documents', 'Downloads': home + '/Downloads'}
        self.ui.Trash.command = 'nautilus trash:///'
        self.ui.Trash.list = {'Empty Trash': 'rm -rf ~/.Trash/*'}
        
        self.lastwins = []
        self.lastclasses = {}
        self.lastshowedwins = []
        self.duped = 0 # the number of grouped windows
        gtk.timeout_add(1000, self.update_wins)
        
        self.set_opacity(0.5)

    def on_winbtn_click(self, widget, data=None):
        print widget.get_label()
        
    def on_click(self, widget, event):
        if event.button == 3:
            print 'right-clicked', widget.get_label()
            for i in widget.list.keys():
                item = gtk.MenuItem(i)
                item.command = widget.list[i]
                item.connect('activate', self.quicklaunch)
                self.ui.quicklist.append(item)
            self.ui.quicklist.button = widget
            self.ui.quicklist.show_all()
            self.ui.quicklist.popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            print 'clicked', widget.get_label()
            
    def quicklaunch(self, widget, data=None):
        print 'Running', widget.command
        if '%s' in widget.get_parent().button.command: os.system(widget.get_parent().button.command % widget.command)
        else: os.system(widget.command)
        
    def update_wins(self):
        print 'Updating...'
        x = 1
        classes = {'File Manager': self.ui.Home}
        
        wins = []
        showedwins = []
        
        for win in getwins():
            if x > 15: 
                print 'DEBUG: Max window limit exceeded!'
                break
            if win.get_window_type().value_nick == "normal" and win.is_on_workspace(screen.get_active_workspace()) and win.get_class_group().get_name() and win.get_pid() not in self.lastwins:
                if win.get_class_group().get_name() in classes.keys():
                    btn = classes[win.get_class_group().get_name()]
                    label = btn.get_label()
                    if label: newlabel = str(int(label) + 1)
                    else: newlabel = '2'
                    btn.set_label(newlabel)
                    print win.get_class_group().get_name(), win.get_pid()
                else:
                    
                    btn = gtk.Button()
                    img = gtk.Image()
                    img.set_from_pixbuf(win.get_icon())
                    btn.set_image(img)
                    btn.set_relief(gtk.RELIEF_NONE)

                    self.ui.topbox.pack_start(btn)
                    btn.show()
                    classes.update({win.get_class_group().get_name(): btn})
                    print win.get_class_group().get_name(), win.get_pid()
                    showedwins += [win.get_pid()]
                x += 1
            wins += [win.get_pid()]

            
        for win in self.lastshowedwins:
            if win not in wins:
                num = self.lastshowedwins.index(win) + 1
                if num
                key = self.lastclasses.keys()[self.lastshowedwins.index(win) + 1]
                print 'removing', key
                self.lastclasses[key].destroy()
            
        if classes and classes != {'File Manager': self.ui.Home}: self.lastclasses = classes
        if wins: self.lastwins = wins
        if showedwins: self.lastshowedwins = showedwins
        return True
        
    def unautohide(self, wid, e):
        print 'Unautohiding (fakishly)'
