# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE
import os
import gettext
import gconf
from ConfigParser import ConfigParser
from gettext import gettext as _
gettext.textdomain('melia')

import gtk, wnck

screen = wnck.screen_get_default()
while gtk.events_pending():
    gtk.main_iteration()


def getwins():
    wins = screen.get_windows()
    return wins
    
import launcher_config
import logging
logger = logging.getLogger('melia')

from melia_lib import Window
from melia.AboutMeliaDialog import AboutMeliaDialog
from melia.PreferencesMeliaDialog import PreferencesMeliaDialog
from melia.MeliaPanelDialog import MeliaPanelDialog



def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    
# See melia_lib.Window.py for more details about how this class works
class MeliaWindow(Window):
    __gtype_name__ = "MeliaWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MeliaWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutMeliaDialog
        self.PreferencesDialog = PreferencesMeliaDialog
        #self.MeliaPanel = MeliaPanelDialog
        
        #set the height
        #print dir(self.ui.melia_window)
        if launcher_config.height == 'default': launcher_config.height = self.get_screen().get_height() - launcher_config.top_panel_height
        self.ui.melia_window.set_size_request(launcher_config.width, self.get_screen().get_height() - launcher_config.top_panel_height)

        # Code for other initialization actions should be added here.
        #color = gtk.gdk.color_parse('#000')
        #self.modify_bg(gtk.STATE_NORMAL, color)  
        #self.ui.layout1.modify_bg(gtk.STATE_NORMAL, color)        
        client = gconf.client_get_default ();


        client.add_dir ("/apps/melia",
                      gconf.CLIENT_PRELOAD_NONE)
        
        # load all the custom quicklists
        self.qls = {}
        for ql in os.listdir('quicklists/'):
            if ql.endswith('.py') and not ql.startswith('_'):
                qlm = my_import('quicklists.' + ql.split('.py')[0])
                self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql)})  
                if 'empty_render' in dir(qlm): self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql, qlm.empty_render)})  
             
        home = os.getenv('HOME')
        l0 = os.listdir('/usr/share/applications')
        l1 = os.listdir(home + '/.local/share/applications')
        for i in launcher_config.pinned.keys():
            if launcher_config.pinned[i] + '.desktop' in l0:
                print '[INFO] Adding %s from pinstack' % launcher_config.pinned[i]
                cf = ConfigParser()
                cf.read('/usr/share/applications/%s.desktop' % launcher_config.pinned[i])
                items = cf.items('Desktop Entry')
                name, swc, command, icon = False, False, False, False
                for c in items:
                    if c[0] == 'name': name = c[1]
                    elif c[0] == 'startupwmclass': swc = c[1]
                    elif c[0] == 'exec': command = c[1]
                    elif c[0] == 'icon': icon = c[1]
                    if command and not swc: swc = launcher_config.pinned[i]
                if swc and command and icon and name:
                    btn = gtk.Button()
                    img = gtk.Image()
                   # print dir(win.get_class_group().get_icon())
                    img.set_from_icon_name(icon, gtk.ICON_SIZE_DND)
                    
                    btn.set_image(img)
                    btn.set_relief(gtk.RELIEF_NONE)
                    btn.win_is_open = False
                    btn.connect('clicked', self.launcher)
                    btn.list = {}
                    
                    btn.command = command
                    btn.empty_render = ''
                    
                    # check for an imported quicklist
                    sc = launcher_config.pinned[i].replace('-', '_')
                    if sc in self.qls.keys():
                        if self.qls[sc][0]: btn.command = self.qls[sc][0]
                        btn.list = self.qls[sc][1]
                        if len(self.qls[sc]) > 2: btn.empty_render = self.qls[sc][2]
                    
                    btn.appname = name
                    btn.connect('button-press-event', self.on_click)
                    btn.win = None
                    self.ui.topbox.pack_start(btn)
                    btn.show()
                else: 
                    print swc, command, icon, name
                
                
            else: 
                print '[DEBUG] No such launcher: %s' % launcher_config.pinned[i] 
                logger.debug('No such launcher: %s' % launcher_config.pinned[i])
                
        


        self.ui.Trash.command = 'nautilus trash:///'
        self.ui.Trash.list = {'Empty Trash': 'rm -rf %s/.local/share/Trash/info/* && rm -rf %s/.local/share/Trash/files/*' % (os.getenv('HOME'), os.getenv('HOME'))}
        self.ui.Trash.appname = 'Trash'
        
        #gtk.timeout_add(1000, self.update_wins)
        
        screen.connect('window-opened', self.add_window)
        screen.connect('window-closed', self.remove_window)
        
        #self.classes = {'File Manager': self.ui.Home}
        self.wins = {}
        for win in getwins():
            #if x > 15: 
            #    print 'DEBUG: Max window limit exceeded!'
            #    break
            if win.get_window_type().value_nick == "normal" and win.is_on_workspace(screen.get_active_workspace()) and not win.is_skip_tasklist():
                xid = None
                for winxid in self.wins.keys():
                    if wnck.window_get(winxid).get_class_group().get_name() == win.get_class_group().get_name():
                        xid = winxid
                if xid:
                    btn = self.wins[xid]
                    label = btn.get_label()
                    if label: newlabel = str(int(label) + 1)
                    else: newlabel = '2'
                    btn.set_label(newlabel)
                    btn.win_is_open = True
                    print win.get_class_group().get_name(), win.get_pid()
                else:
                    
                    btn = gtk.Button()
                    img = gtk.Image()
                   # print dir(win.get_class_group().get_icon())
                    img.set_from_pixbuf(win.get_class_group().get_icon())
                    btn.set_image(img)
                    btn.set_relief(gtk.RELIEF_NONE)
                    btn.win_is_open = True
                    btn.connect('clicked', self.minmaxer)
                    btn.list = {}
                    
                    btn.empty_render = ''
                    
                    # check for an imported quicklist
                    sc = win.get_application().get_name().lower().replace(' ', '_').replace('-', '_')
                    if sc in self.qls.keys():
                        if self.qls[sc][0]: btn.command = self.qls[sc][0]
                        btn.list = self.qls[sc][1]
                        if len(self.qls[sc]) > 2: btn.empty_render = self.qls[sc][2]
                    
                    btn.appname = win.get_name()
                    btn.connect('button-press-event', self.on_click)
                    btn.win = win
                    self.ui.topbox.pack_start(btn)
                    btn.show()
                    #self.classes.update({win.get_class_group().get_name(): btn})
                    self.wins.update({win.get_xid(): btn})
                    print win.get_class_group().get_name(), win.get_pid()
                   # showedwins += [win.get_pid()]
        

    def on_winbtn_click(self, widget, data=None):
        print widget.get_label()
        
    def on_click(self, widget, event):
        if event.button == 3:
            self.ui.quicklist = gtk.Menu() # clear the menu each time
            print 'right-clicked', widget.appname
            for i in widget.list.keys():
                item = gtk.MenuItem(i)
                item.command = widget.list[i]
                item.connect('activate', self.quicklaunch)
                self.ui.quicklist.append(item)
            self.ui.quicklist.append(gtk.SeparatorMenuItem())
            item = gtk.MenuItem("Launcher Preferences")
            item.connect('activate', self.on_mnu_preferences_activate)
            self.ui.quicklist.append(item)
            item = gtk.MenuItem("Close")
            self.ui.quicklist.append(item)
            self.ui.quicklist.button = widget
            self.ui.quicklist.show_all()
            self.ui.quicklist.popup(None, None, None, event.button, event.time)
        elif event.button == 1:
            print 'clicked', widget.get_label()
        panel = MeliaPanelDialog()
        panel.run()
            
    def quicklaunch(self, widget, data=None):
        print 'Running', widget.command
        if '%s' in widget.get_parent().button.command: os.system(widget.get_parent().button.command % widget.command)
        else: os.system(widget.command)
        
        
    def add_window(self, screen, win):
        print 'adding', win.get_name()
        if win.get_window_type().value_nick == "normal" and win.is_on_workspace(screen.get_active_workspace()) and not win.is_skip_tasklist():
            xid = None
            for winxid in self.wins.keys():
                if wnck.window_get(winxid).get_class_group().get_name() == win.get_class_group().get_name():
                    xid = winxid
            if xid:
                btn = self.wins[xid]
                label = btn.get_label()
                if label: newlabel = str(int(label) + 1)
                else: newlabel = '2'
                btn.set_label(newlabel)
                btn.win_is_open = True
                print win.get_class_group().get_name(), win.get_pid()
            else:
                btn = gtk.Button()
                img = gtk.Image()
                img.set_from_pixbuf(win.get_icon())
                btn.set_image(img)
                btn.set_relief(gtk.RELIEF_NONE)
                btn.win_is_open = True
                btn.connect('clicked', self.minmaxer)
                btn.win = win
                self.ui.topbox.pack_start(btn)
                btn.list = {}
                
                # check for an imported quicklist
                sc = win.get_application().get_name().lower().replace(' ', '_').replace('-', '_')
                if sc in self.qls.keys():
                    if self.qls[sc][0]: btn.command = self.qls[sc][0]
                    btn.list = self.qls[sc][1]
                        
                btn.appname = win.get_name()
                btn.connect('button-press-event', self.on_click)
                btn.show()
                #self.classes.update({win.get_class_group().get_name(): btn})
                self.wins.update({win.get_xid(): btn})
                print win.get_class_group().get_name(), win.get_pid()
                
    def remove_window(self, screen, win):
        if win.get_xid() in self.wins.keys():
            print 'removing', win.get_name()
            btn = self.wins[win.get_xid()]
            if btn.get_label(): # there's more than one
                print 'theres more than one'
            else: # remove the button
                btn.destroy()
            self.wins.pop(win.get_xid())
        
    def minmaxer(self, widget, event=None):
        win = widget.win
        if not win.is_minimized():
            win.minimize()
        else: 
            win.unminimize(gtk.get_current_event_time())

    def unautohide(self, wid, e):
        print 'Unautohiding (fakishly)'
        
        
    def launcher(self, wid, e=None):
        print 'Launching ' + wid.command
        if '%s' in wid.command: os.system(wid.command % wid.empty_render)
        else: os.system(wid.command)
        
        
