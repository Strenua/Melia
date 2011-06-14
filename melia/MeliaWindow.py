# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE
import os
import gettext
import gconf
import cairo
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
from melia_lib import melia_dbus
from melia.AboutMeliaDialog import AboutMeliaDialog
from melia.PreferencesMeliaDialog import PreferencesMeliaDialog
from melia.MeliaPanelDialog import MeliaPanelDialog
from melia.MeliaDashboardDialog import MeliaDashboardDialog
from melia_lib.preferences import preferences
from indicators import system

def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    
global buttons
buttons = []
class Button(gtk.Button): # my cool buttons ;)
    def finish_initializing(self, window_title='wind0w'): 
        global buttons
        buttons += [self]
        # shorten the title
        if len(window_title) > 20: window_title = window_title[:19] + '...'
        self.window_title = window_title
        # figure out the button style from config
        if preferences['button_style'] == 0: return # for now, i'll just do nothing here :P
        
        else: 
            # set width
            self.set_size_request(200, 32)
            # add the label
            self.set_label(window_title)

    def update_style(self):
        # figure out the button style from config
        if preferences['button_style'] == 0: 
            self.set_size_request(int(preferences['launcher_width']), 48)
            self.set_label('')        
        
        else: 
            # set width
            self.set_size_request(200, 32)
            # add the label
            self.set_label(self.window_title)
            
    
            
   
# test couchdb...
preferences.db_connect()
preferences.load()

def transparent_expose(widget, event):
	cr = widget.window.cairo_create()
	cr.set_operator(cairo.OPERATOR_CLEAR)
	region = gtk.gdk.region_rectangle(event.area)
	cr.region(region)
	cr.fill()
	return False

# See melia_lib.Window.py for more details about how this class works
class MeliaWindow(Window):
    __gtype_name__ = "MeliaWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MeliaWindow, self).finish_initializing(builder)

        self.AboutDialog = AboutMeliaDialog
        self.PreferencesDialog = PreferencesMeliaDialog
        #self.MeliaPanel = MeliaPanelDialog
        
        #set the height/orientation/position
        #print dir(self.ui.melia_window)
        if preferences['launcher_height'] == 'default': preferences['launcher_height'] = float(self.get_screen().get_height() - int(preferences['top_panel_height']))
        self.ui.melia_window.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        self.move(0, int(preferences['top_panel_height']))
        self.set_orientation()
                
            
        # Code for other initialization actions should be added here.
        #color = gtk.gdk.color_parse('#000')
        #self.modify_bg(gtk.STATE_NORMAL, color)  
        #self.ui.layout1.modify_bg(gtk.STATE_NORMAL, color)        
        #client = gconf.client_get_default ();


        #client.add_dir ("/apps/melia",
        #              gconf.CLIENT_PRELOAD_NONE)
        
        # load all the custom quicklists
        self.qls = {}
        self.update_qls() 
             
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
                    elif c[0] == 'exec': command = c[1].replace('%U', '').replace('%u', '')
                    elif c[0] == 'icon': icon = c[1]
                    if command and not swc: swc = launcher_config.pinned[i]
                if swc and command and icon and name:
                    btn = Button()
                    btn.finish_initializing(name)
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
        gtk.timeout_add(100, self.start_panel)

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
                    #btn.set_label(newlabel)
                    btn.win_is_open = True
                    print win.get_class_group().get_name(), win.get_pid()
                else:
                    
                    btn = Button()
                    btn.finish_initializing(win.get_name())
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
                   
        melia_dbus.start_loop(self)
        self.get_toplevel().show() # must call show() before property_change()
        
        self.get_toplevel().window.property_change("_NET_WM_STRUT", 
            "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, [48, 0, preferences['top_panel_height'], 0])       
        self.move(0, int(preferences['top_panel_height']))  
        self.notification_in_progress = False
        self.notification_stack = {}
        
           
    def widgefy(self, widget, e=False):
        
        if e: widget.set_position(gtk.WIN_POS_CENTER)
		if e: widget.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
		if e: widget.set_keep_below(True)
		if e: widget.set_decorated(False)
		if e: widget.stick()

		screen = widget.get_screen()
		rgba = screen.get_rgba_colormap()
		widget.set_colormap(rgba)
		widget.set_app_paintable(True)
		widget.connect("expose-event", transparent_expose)
		color = gtk.gdk.color_parse('#000')
        widget.modify_text(gtk.STATE_NORMAL, color)  
        #widget.modify_font(color) 
		widget.show()
        
        
    def start_panel(self):
        self.panel = MeliaPanelDialog()
        self.panel.show() 
        # after the panel is up, load indicators
        sysi = system.SystemIndicator()      
        sysi.append_to_stack()
        self.panel.ui.dashbutton.set_size_request(int(preferences['launcher_width']), -1)
        self.dash = MeliaDashboardDialog()
        self.dash.hide()
        #
        self.desk = MeliaDashboardDialog()
        self.desk.mode = 'desk'
        self.widgefy(self.desk, True)
        self.widgefy(self.desk.ui.vbox1)
        self.widgefy(self.desk.ui.scrolledwindow1)
        self.widgefy(self.desk.ui.viewport1)
        self.widgefy(self.desk.ui.table3)
        self.widgefy(self.desk.ui.entry1)
        self.widgefy(self.desk.ui.media_apps_button)
        #
        self.panel.ui.dashbutton.connect('toggled', self.show_dash)
        ### TODO: REMOVE THIS AND FIX THE IMAGE SETTER!
        #self.panel.ui.notification_icon.hide()
        
        ###############################################
        
    def show_dash(self, widget, data=None):
        if not widget.get_active(): 
            self.dash.hide()
        else:
            self.dash.move(int(preferences['launcher_width']), int(preferences['top_panel_height']))
            self.dash.show()
            self.dash.move(int(preferences['launcher_width']), int(preferences['top_panel_height']))
        #self.dash.connect('focus', self.hide_dash)
        #self.dash.set_events(gtk.gdk.FOCUS_CHANGE_MASK)
        
    def hide_dash(self, widget, data=None):
        self.dash.hide()
        self.panel.ui.dashbutton.set_state(gtk.STATE_NORMAL)
        
    def update_qls(self):
        for ql in os.listdir('quicklists/'):
            if ql.endswith('.py') and not ql.startswith('_'):
                qlm = my_import('quicklists.' + ql.split('.py')[0])
                self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql)})  
                if 'empty_render' in dir(qlm): self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql, qlm.empty_render)}) 
                
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
            print 'BLABLA:', self.ui.quicklist.menu_get_for_attach_widget()
        elif event.button == 1:
            print 'clicked', widget.get_label()
        
            
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
                btn = Button()
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
        
    def set_orientation(self):
        orientation = preferences['orientation']
        if int(orientation) == 1: 
            self.ui.vbox1.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.ui.topbox.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.ui.bottombox.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.move(preferences['launcher_x_pos'], preferences['launcher_y_pos'])
        else: 
            self.ui.vbox1.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.ui.topbox.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.ui.bottombox.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.move(preferences['launcher_x_pos'], preferences['launcher_y_pos'])
            
    def update_height(self):
        self.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        
    def update_width(self):
        self.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        
    def update_button_style(self):
        for button in buttons:
            button.update_style()
            
            
    def show_notification(self, id, icon, summary, body, timeout):
        #print 'ICON:', icon
        if timeout > 10000: timeout = 10000
        if self.notification_in_progress and self.notification_in_progress != id: self.notification_stack.update({id: (id, icon, summary, body, timeout)})
        else: 
            self.panel.ui.notification_area.set_label('%s: %s' % (summary, body))
            if icon:
                #self.panel.ui.notification_icon = gtk.Image()
                self.panel.ui.notification_icon.set_from_icon_name(icon)
                self.panel.ui.notification_icon.show()

            print 'setting timeout to', timeout 
            gtk.timeout_add(timeout, self.notification_expire)
            self.notification_in_progress = id
        
    def notification_expire(self):
        print 'notification expiring'
        self.notification_in_progress = None
        self.panel.ui.notification_area.set_label('')
        if self.notification_stack: 
            for n in self.notification_stack.keys():
                nf = self.notification_stack[n]
                del(self.notification_stack[n])
                self.show_notification(nf[0], nf[1], nf[2], nf[3], nf[4])
