3# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
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
### TODO[s]:
# Support libindicate
# Support Unity quicklists
# 
###
import os
import sys
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
    
import logging
logger = logging.getLogger('melia')

from melia_lib import Window
from melia_lib import melia_dbus
from melia_lib import meliaconfig
from melia.AboutMeliaDialog import AboutMeliaDialog
from melia.PreferencesMeliaDialog import PreferencesMeliaDialog
from melia.MeliaPanelDialog import MeliaPanelDialog
from melia.MeliaDashboardDialog import MeliaDashboardDialog
from melia_lib.preferences import preferences
#from indicators import system

def my_import(name):
    mod = __import__(name)
    components = name.split('.')
    for comp in components[1:]:
        mod = getattr(mod, comp)
    return mod
    
print 'PID:', os.getpid()
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
        if preferences['button_style'] < 1: return # for now, i'll just do nothing here :P
        
        else: 
            # set width
            self.set_size_request(200, 32)
            # add the label
            self.set_label(window_title)    
        if preferences['button_relief'] == 0: self.set_relief(gtk.RELIEF_NONE)
        elif preferences['button_relief'] == 1: self.set_relief(gtk.RELIEF_HALF)

    def update_style(self):
        # figure out the button style from config
        if preferences['button_style'] < 1: 
            self.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_width']))
            self.set_label('')        
        
        else: 
            # set width
            self.set_size_request(200, 32)
            # add the label
            self.set_label(self.window_title)
    def notify(self):
        self.ncount = 0
        gtk.timeout_add(500, self.toggle)
        
    def toggle(self):
        if self.get_state() == gtk.STATE_PRELIGHT: self.set_state(gtk.STATE_SELECTED)
        else: self.set_state(gtk.STATE_PRELIGHT)
        if self.ncount >= 9: self.set_state(gtk.STATE_NORMAL)
        self.ncount += 1
        return self.ncount < 10
    
def transparent_expose(widget, event):
	cr = widget.window.cairo_create()
	cr.set_operator(cairo.OPERATOR_CLEAR)
	region = gtk.gdk.region_rectangle(event.area)
	cr.region(region)
	cr.fill()
	return False

DATA_DIR = meliaconfig.__melia_data_directory__.replace('..', os.getcwd())
sys.path += [DATA_DIR]
import indicators

try:
    if 'run' not in sys.argv and 'melia' not in sys.argv: exit()
    for e in os.environ:
        if 'root' in os.getenv(e): exit()
except: pass

# See melia_lib.Window.py for more details about how this class works
class MeliaWindow(Window):
    __gtype_name__ = "MeliaWindow"
    melia_dbus.run()   
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(MeliaWindow, self).finish_initializing(builder)
        self.AboutDialog = AboutMeliaDialog
        self.PreferencesDialog = PreferencesMeliaDialog
        #self.MeliaPanel = MeliaPanelDialog
        
        # connect to couchdb
        preferences.db_connect()
        preferences.load()
        
        #set the height/orientation/position
        #print dir(self.ui.melia_window)
        if preferences['launcher_height'] == 'default': 
            preferences['launcher_height'] = float(self.get_screen().get_height() - int(preferences['top_panel_height']))
        self.ui.melia_window.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        self.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
        self.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
        self.set_orientation()
                
            
        # Code for other initialization actions should be added here.
        if preferences['custom_colors']:
            gtk.rc_parse(DATA_DIR + '/ui/melia-quiet.rc')
        #self.ui.layout1.modify_bg(gtk.STATE_NORMAL, color)        
        #client = gconf.client_get_default ();


        #client.add_dir ("/apps/melia",
        #              gconf.CLIENT_PRELOAD_NONE)
        
        # load all the custom quicklists
        self.qls = {}
        self.update_qls() 
        self.btns = []  
        #self.ui.Trash. #TODO: add the trash button to self.btns
        home = os.getenv('HOME')
        l0 = os.listdir('/usr/share/applications')
        l1 = os.listdir(home + '/.local/share/applications')
        for i in preferences['pinned'].keys():
            if preferences['pinned'][i] + '.desktop' in l0:
                logger.debug('Adding %s from pinstack' % preferences['pinned'][i])
                cf = ConfigParser()
                cf.read('/usr/share/applications/%s.desktop' % preferences['pinned'][i])
                items = cf.items('Desktop Entry')
                name, swc, command, icon = False, False, False, False
                for c in items:
                    if c[0] == 'name': name = c[1]
                    elif c[0] == 'startupwmclass': swc = c[1]
                    elif c[0] == 'exec': command = c[1].replace('%U', '').replace('%u', '')
                    elif c[0] == 'icon': icon = c[1]
                    if command and not swc: swc = preferences['pinned'][i]
                if swc and command and icon and name:
                    btn = Button()
                    btn.finish_initializing(name)
                    img = gtk.Image()
                   # print dir(win.get_class_group().get_icon())
                    img.set_from_icon_name(icon, gtk.ICON_SIZE_DND)
                    
                    btn.set_image(img)
                    #btn.set_relief(gtk.RELIEF_NONE)
                    btn.win_is_open = False
                    btn.connect('clicked', self.launcher)
                    btn.list = {}
                    if preferences['orientation'] == 0: btn.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_width']))
                    else: btn.set_size_request(int(preferences['launcher_height']), int(preferences['launcher_height']))
                    
                    btn.command = command
                    btn.empty_render = ''
                    
                    # check for an imported quicklist
                    sc = preferences['pinned'][i].replace('-', '_')
                    if sc in self.qls.keys():
                        if self.qls[sc][0]: btn.command = self.qls[sc][0]
                        btn.list = self.qls[sc][1]
                        if len(self.qls[sc]) > 2: btn.empty_render = self.qls[sc][2]
                    
                    btn.appname = name
                    btn.connect('button-press-event', self.on_click)
                    btn.win = None
                    self.ui.topbox.pack_start(btn)
                    btn.show()
                    self.btns.append(btn)
                    
                    
                else: 
                    logger.warn('Could not find necessary information for .desktop file. swc: %s, command: %s, icon: %s, name: %s' % (swc, command, icon, name))
                
                
            else: 
                logger.debug('No such launcher: %s' % preferences['pinned'][i])
        gtk.timeout_add(5, self.start_panel)

        self.ui.Trash.command = 'nautilus trash:///'
        self.ui.Trash.list = {'Empty Trash': 'rm -rf %s/.local/share/Trash/info/* && rm -rf %s/.local/share/Trash/files/*' % (os.getenv('HOME'), os.getenv('HOME'))}
        self.ui.Trash.appname = 'Trash'
        
        #gtk.timeout_add(1000, self.update_wins)
        
        screen.connect('window-opened', self.add_window)
        screen.connect('window-closed', self.remove_window)
        
        #self.classes = {'File Manager': self.ui.Home}
        self.wins = {}
        #self.btns = []
        for win in getwins():
            self.add_window(screen, win)
                   
        #melia_dbus.init(self)
        #melia_dbus.run()
        self.get_toplevel().show() # must call show() before property_change()
        if preferences['orientation'] == 0: screenshove = [int(preferences['launcher_width']), 0, int(preferences['top_panel_height']), 0]
        else: screenshove = [0, 0, int(preferences['top_panel_height']), int(preferences['launcher_height'])]
        print screenshove
        if not preferences['autohide_launcher']:
            self.get_toplevel().window.property_change("_NET_WM_STRUT", 
                "CARDINAL", 32, gtk.gdk.PROP_MODE_REPLACE, screenshove)       
        #self.move(0, int(preferences['launcher_y_pos']))  
        self.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
        self.notification_in_progress = False
        self.notification_stack = {}
        self.notification_submenu = gtk.Menu()
        self.keep_launcher = False
        if preferences['autohide_launcher']:
            gtk.timeout_add(4000, self.start_autohide)
            
            ahwin = gtk.Window()
            ahwin.set_size_request(10, int(preferences['launcher_height']))
            ahwin.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
            ahwin.set_decorated(False)
            self.widgefy(ahwin)
            ahwin.show()
            ahwin.connect('enter-notify-event', self.ah_show)
            ahwin.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
            ahwin.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DOCK)
            #self.widgefy(ahwin)
            
            self.connect('leave-notify-event', self.start_autohide)
        #screen.connect('MOTION_LEFT', self.ah_show)
        
        self.launcher = self
        
        # load extensions... after a 100ms delay just to be safe
        gtk.timeout_add(100, self.load_extensions)
        
        # save changes to preferences
        preferences.save()
        
        
    
    #### AUTOHIDE FUNCTIONS ####
    def start_autohide(self, w=None, d=None):
        if self.keep_launcher and d != True: return False
        #print self.keep_launcher, d
        self.keep_launcher = False
        self.autohide_move_count = 0
        gtk.timeout_add(7, self.do_hide)
        #self.connect(gtk.
    
    def do_hide(self):
        self.autohide_move_count += 1
        x, y = self.get_position()
        self.move(x - 1, y)
        if self.autohide_move_count <= preferences['launcher_width'] + 14: return True
        else:
            # make sure its in the right position
            self.move(0 - int(preferences['launcher_width']), int(preferences['top_panel_height']))
            return False
        
    def do_unhide(self):
        self.autohide_move_count += 1
        x, y = self.get_position()
        self.move(x + 1, y)
        if self.autohide_move_count <= preferences['launcher_width'] + 14: return True
        else:
            # make sure its in the right position
            self.move(0, int(preferences['top_panel_height']))
            return False
    
    def ah_show(self, widget, data=None):
        self.autohide_move_count = 0
        gtk.timeout_add(7, self.do_unhide)
        #gtk.timeout_add(4500, self.start_autohide)
        
    ############################
        
    #### DESKTOP/DASH FUNCTIONS ####   
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
		#color = gtk.gdk.color_parse('#000')
        #widget.modify_text(gtk.STATE_NORMAL, color)  
        #widget.modify_font(color) 
		widget.show()
    def show_deskdash(self):
        if preferences['desktop_dash']:
            self.desk = MeliaDashboardDialog()
            self.desk.parent = self
            self.desk.mode = 'desk'
            self.widgefy(self.desk, True)
            self.widgefy(self.desk.ui.vbox1)
            self.widgefy(self.desk.ui.scrolledwindow1)
            self.widgefy(self.desk.ui.viewport1)
            self.widgefy(self.desk.ui.table3)
            self.widgefy(self.desk.ui.entry1)
            self.widgefy(self.desk.ui.media_apps_button)
            if not preferences['orientation']: self.desk.move(int(preferences['launcher_width']), int(preferences['top_panel_height'])) 
        else: 
            pass#self.desk.destroy() 
            
    def show_dash(self, widget, data=None):
        if not widget.get_active(): 
            self.dash.hide()
        else:
            if hasattr(self, 'desk'): self.desk.parent = self
            self.dash.move(int(preferences['launcher_width']), int(preferences['top_panel_height']))
            self.dash.show()
            if preferences['orientation'] == 0: self.dash.move(int(preferences['launcher_width']), int(preferences['top_panel_height']))
            else: self.dash.move(0, int(preferences['top_panel_height']))
            if preferences['autohide_launcher']: self.dash.move(0, int(preferences['top_panel_height']))
            self.dash.set_can_focus(True)
            self.dash.ui.entry1.set_can_focus(True)
            self.dash.ui.entry1.activate()
        #self.dash.connect('focus', self.hide_dash)
        #self.dash.set_events(gtk.gdk.FOCUS_CHANGE_MASK)
        
    def hide_dash(self, widget, data=None):
        self.dash.hide()
        self.panel.ui.dashbutton.set_state(gtk.STATE_NORMAL)  
    ########################################
    
    #### PANEL FUNCTIONS ####  
    def start_panel(self):
        self.panel = MeliaPanelDialog()
        self.panel.show() 
        
        if preferences['orientation'] == 0: self.panel.ui.dashbutton.set_size_request(int(preferences['launcher_width']), -1)
        else: self.panel.ui.dashbutton.set_size_request(48, -1)
        self.dash = MeliaDashboardDialog()
        self.dash.hide()
        self.dash.parent = self
        #
        if preferences['desktop_dash']: self.show_deskdash()
        #
        self.panel.ui.dashbutton.connect('toggled', self.show_dash)
        ### TODO: REMOVE THIS AND FIX THE IMAGE SETTER!
        #self.panel.ui.notification_icon.hide()
        #self.panel.ui.notification_icon.hide()
        
    ###############################################
    
    #### LAUNCHER BUTTONS/QUICKLISTS ####    
    def update_qls(self):
        for ql in os.listdir(DATA_DIR + '/quicklists/'):
            if ql.endswith('.py') and not ql.startswith('_'):
                qlm = my_import('quicklists.' + ql.split('.py')[0])
                self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql)})  
                if 'empty_render' in dir(qlm): self.qls.update({ql.split('.py')[0]: (qlm.command, qlm.ql, qlm.empty_render)}) 
                
    def on_winbtn_click(self, widget, data=None):
        print widget.get_label()
        
    def on_click(self, widget, event):
        logger.debug('clicked button at x, y:', self.get_button_position(widget))
        if event.button == 3:
            self.ui.quicklist = gtk.Menu() # clear the menu each time
            logger.debug('right-clicked', widget.appname)
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
            self.ui.quicklist.btn = widget
            self.ui.quicklist.popup(None, None, self.set_ql_pos, event.button, event.time)
            if preferences['autohide_launcher']: self.ui.quicklist.connect('deactivate', self.start_autohide, True)
            self.keep_launcher = True
            
            #logger.debug('BLABLA:', self.ui.quicklist.menu_get_for_attach_widget())
        elif event.button == 1:
            logger.debug('clicked', widget.get_label())
        
    def get_button_position(self, button):
        wx, wy = self.get_position()
        bx = 0
        #bsrx, bsry = button.get_size_request()
        #if bsry < 2: # ignore it and guess based on button style
        if preferences['button_style'] < 1: bsry = preferences['launcher_width'] - 4
        elif preferences['button_style'] == 1: bsry = 28
        by = ((self.btns.index(button) * bsry) + (4 * self.btns.index(button))) + wy
        return bx, by
        
    def set_ql_pos(self, menu, data=None):
        x, y = self.get_button_position(menu.btn)
        
        if preferences['orientation'] == 0: x += int(preferences['launcher_width'] + preferences['launcher_x_pos'])
        else:
            wx, wy = self.get_position()
            
            menuheight = 0
            for c in menu.get_children():
                if type(c) == gtk.SeparatorMenuItem: 
                    menuheight += 4
                else: menuheight += 17
            y = wy - preferences['launcher_height'] - menuheight
            
            if preferences['button_style'] < 1: bsrx = 81
            elif preferences['button_style'] == 1: bsrx = 240
            x = ((self.btns.index(menu.btn) * bsrx) + (4 * self.btns.index(menu.btn))) + wx
            
        print x, y
        return int(x), int(y), True
                
    def quicklaunch(self, widget, data=None):
        logger.debug('Running', widget.command)
        if '%s' in widget.get_parent().button.command: os.system(widget.get_parent().button.command % widget.command)
        else: os.system(widget.command)
        
    # add a launcher button    
    def add_window(self, screen, win):
        logger.debug('adding', win.get_name())
        if win.get_window_type().value_nick == "normal" and win.is_on_workspace(screen.get_active_workspace()) and not win.is_skip_tasklist():
            xid = None
            try: 
                for winxid in self.wins.keys():
                    if wnck.window_get(winxid).get_class_group().get_name() == win.get_class_group().get_name():
                        xid = winxid
            except AttributeError: logger.warn('Cannot get window class')
            if xid:
                btn = self.wins[xid]
                label = btn.get_label()
                if label: newlabel = str(int(label) + 1)
                else: newlabel = '2'
                btn.set_label(newlabel)
                btn.win_is_open = True
                #print win.get_class_group().get_name(), win.get_pid()
            else:
                btn = Button()
                btn.finish_initializing()
                img = gtk.Image()
                icon = win.get_icon()
                #icon.scale(icon, preferences['launcher_width'], preferences['launcher_width'], preferences['launcher_width'], preferences['launcher_width'], 0, 0, 5, 5, 0)
                img.set_from_pixbuf(icon)
                
                if preferences['orientation'] == 0: 
                    btn.set_size_request(int(preferences['launcher_width']) - 10, int(preferences['launcher_width']))
                    img.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_width']))
                    img.set_pixel_size(int(preferences['launcher_width']) - 5)
                else: 
                    btn.set_size_request(int(preferences['launcher_height']) - 5, int(preferences['launcher_height']))
                    img.set_size_request(int(preferences['launcher_height']), int(preferences['launcher_height']))
                    img.set_pixel_size(int(preferences['launcher_height']) - 10)
                btn.set_image(img)
                #btn.set_relief(gtk.RELIEF_NONE)
                                
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
                #btn.show()
                #self.classes.update({win.get_class_group().get_name(): btn})
                self.wins.update({win.get_xid(): btn})
                #print win.get_class_group().get_name(), win.get_pid()
                self.btns.append(btn)
                #style = btn.get_style().copy()
                #style.bg[gtk.STATE_NORMAL] = gtk.gdk.color_parse('#F07746')
                #print str(style.props)
                #btn.set_style(style)
                btn.show()
                btn.notify()
                
    def remove_window(self, screen, win):
        if win.get_xid() in self.wins.keys():
            logger.debug('removing', win.get_name())
            btn = self.wins[win.get_xid()]
            if btn.get_label(): # there's more than one
                btn.set_label(str(int(button.get_label() - 1)))
            else: # remove the button
                btn.destroy()
                self.btns.pop(self.btns.index(btn))
            self.wins.pop(win.get_xid())
        
    def minmaxer(self, widget, event=None):
        win = widget.win
        if not win.is_minimized() and win.is_active():
            win.minimize()
        elif not win.is_minimized() and not win.is_active(): 
            win.activate(gtk.get_current_event_time())
        else: win.unminimize(gtk.get_current_event_time())
    # launcher for quicklists    
    def launcher(self, wid, e=None):
        print 'Launching ' + wid.command
        if '%s' in wid.command: os.system(wid.command % wid.empty_render)
        else: os.system(wid.command)
    ######################################
    
    #### PREFERENCE LIVE-UPDATE FUNCTIONS ####
    def set_orientation(self):
        orientation = preferences['orientation']
        if int(orientation) == 1: 
            self.ui.vbox1.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.ui.topbox.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.ui.bottombox.set_orientation(gtk.ORIENTATION_HORIZONTAL)
            self.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
        else: 
            self.ui.vbox1.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.ui.topbox.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.ui.bottombox.set_orientation(gtk.ORIENTATION_VERTICAL)
            self.move(int(preferences['launcher_x_pos']), int(preferences['launcher_y_pos']))
            
    def update_height(self):
        #if preferences['launcher_height'] == 'default': preferences['launcher_height'] = float(self.get_screen().get_height() - int(preferences['top_panel_height']))
        self.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        
    def update_width(self):
        #if preferences['launcher_height'] == 'default': preferences['launcher_height'] = float(self.get_screen().get_height() - int(preferences['top_panel_height']))O
        self.set_size_request(int(preferences['launcher_width']), int(preferences['launcher_height']))
        
    def update_button_style(self):
        for button in buttons:
            button.update_style()
    
    # FIXME: panel does not go completely transparent... :\
    def set_transparent(self): # make the panel transparent
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, "Sorry, Melia does not fully support panel transparency at this point, so it has been disabled")
        md.run()
        md.destroy()
    ##########################################
    
    #### NOTIFICATION FUNCTIONS ####
    # TODO: Move this to MeliaPanelDialog.py
    def show_notification(self, id, icon, summary, body, timeout):
        #print 'ICON:', icon
        if timeout > 15000: timeout = 15000
        elif timeout < 5000: timeout = 5000
        if self.notification_in_progress and self.notification_in_progress != id: self.notification_stack.update({id: (id, icon, summary, body, timeout)})
        else: 
            self.panel.ui.notification_mi.set_label(summary)
            self.panel.ui.notification_mi.set_state(gtk.STATE_SELECTED)
            
            bodyi = gtk.ImageMenuItem()
            bodyi.set_label(body)
            self.notification_submenu.append(bodyi)
            self.panel.ui.notification_mi.set_submenu(self.notification_submenu)
            self.panel.ui.notification_mi.show_all()
            
            if icon:
                #self.panel.ui.notification_icon = gtk.Image()
               # print icon
                im = gtk.image_new_from_icon_name(icon)
                self.panel.ui.notification_mi.set_image(im)
               
            self.panel.ui.notification_mi.show()
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
                
    ##########################################            
    
    #### EXTENSION MANAGEMENT ####
    # After *everything*, load extensions so they can modify whatever they want
    
    def load_extensions(self):
        for extension in preferences['extensions']:
            #try: 
                em = my_import('extensions.' + extension)
                em.main(self)
            #except: 
            #    logger.warn('Failed to load extension: ' + extension)
            

        
