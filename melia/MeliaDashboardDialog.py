# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gtk
import dbus
import os
import subprocess

from melia_lib.helpers import get_builder

import gettext
from gettext import gettext as _
gettext.textdomain('melia')

import logging
logger = logging.getLogger('melia')

from os.path import split
from urllib2 import quote, splittype
from ConfigParser import ConfigParser

if os.path.exists('/usr/bin/plexydesk'): os.system('plexydesk &')
else: 
    a = raw_input('I suggest installing PlexyDesk to accompany Melia. Would you like to try installing it now? [Y/n]')
    if a.lower() == 'y' or a == '': 
        print 'Adding plexydesk nightly PPA...'
        subprocess.call('sudo add-apt-repository ppa:plexydesk/plexydesk-dailybuild'.split())
        print 'Updating software sources...'
        subprocess.call('sudo apt-get update')
        print 'If all of that was successful, now installing plexydesk'
        subprocess.call('sudo apt-get install -y libqt4-declarative-folderlistmodel plexydesk')
        print 'Done! Starting PlexyDesk!'
        os.system('plexydesk &')
        
        
    else: print 'Okay, then if you\'d ever like to, clone git://github.com/siraj/plexydesk.git'


class MeliaDashboardDialog(gtk.Window):
    __gtype_name__ = "MeliaDashboardDialog"
    mode = 'dash'
    parent = None

    def __new__(cls):
        """Special static method that's automatically called by Python when 
        constructing a new instance of this class.
        
        Returns a fully instantiated MeliaDashboardDialog object.
        """
        builder = get_builder('MeliaDashboardDialog')
        new_object = builder.get_object('melia_dashboard_dialog')
        new_object.finish_initializing(builder)
        return new_object

    def finish_initializing(self, builder):
        """Called when we're finished initializing.

        finish_initalizing should be called after parsing the ui definition
        and creating a MeliaDashboardDialog object with it in order to
        finish initializing the start of the new MeliaDashboardDialog
        instance.
        """
        # Get a reference to the builder and set up the signals.
        self.builder = builder
        self.ui = builder.get_ui(self)
        
        self.ui.entry1.connect('changed', self.search)
        
        bus = dbus.SessionBus()
        
        if bus.request_name('org.freedesktop.Tracker1') == dbus.bus.REQUEST_NAME_REPLY_IN_QUEUE:
            tracker_object = bus.get_object('org.freedesktop.Tracker1', '/org/freedesktop/Tracker1/Resources')
            self.tracker = dbus.Interface(tracker_object, 'org.freedesktop.Tracker1.Resources') 
        else:
            logger.warn('Could not connect to Tracker')
            self.loaded = False
            return 
			
        self.split     = split
		self.quote     = quote
		self.splittype = splittype
		
		# save the default buttons to a list so they can be hidden and easily restored after searches
		self.default_buttons = [self.ui.media_apps_button, self.ui.internet_apps_button, self.ui.more_apps_button, self.ui.find_files_button, self.ui.firefox_button, self.ui.shotwell_button, self.ui.evolution_button, self.ui.banshee_button]
		# create an empty list for clearing other buttons
		self.current_buttons = []
		
		gtk.timeout_add(100, self.init_bottom_toolbar)
		
		#self.parent.launcher_index = []
		gtk.timeout_add(100, self.index_launchers)
	
	def index_launchers(self):
	    self.parent.launcher_index = []
	    for desktop in os.listdir('/usr/share/applications/'):
	        if desktop.endswith('.desktop'): 
                cf = ConfigParser()
                cf.read('/usr/share/applications/' + desktop)
               # print '/usr/share/applications/' + desktop
                try: items = cf.items('Desktop Entry')
                except: raise NameError('no [Desktop Entry] section in %s' % '/usr/share/applications/' + desktop)
                name, command, icon = False, False, False
                for c in items:
                    if c[0] == 'name': name = c[1]
                    elif c[0] == 'icon': icon = c[1]
                    elif c[0] == 'exec': command = c[1].replace('%U', '').replace('%u', '')
                if icon and name and command:
	                self.parent.launcher_index += [(name, icon, command)]
	            
        for desktop in os.listdir(os.getenv('HOME') + '/.local/share/applications/'):
	        if desktop.endswith('.desktop'): 
                cf = ConfigParser()
                cf.read(os.getenv('HOME') + '/.local/share/applications/' + desktop)
               # print '~/.local/share/applications/' + desktop
                try: items = cf.items('Desktop Entry')
                except: logger.warn('no [Desktop Entry] section in %s' % os.getenv('HOME') + '/.local/share/applications/' + desktop)
                name, command, icon = False, False, False
                for c in items:
                    if c[0] == 'name': name = c[1]
                    elif c[0] == 'icon': icon = c[1]
                    elif c[0] == 'exec': command = c[1].replace('%U', '').replace('%u', '')
                if icon and name and command:
	                self.parent.launcher_index += [(name, icon, command)]
		
    def init_bottom_toolbar(self):
        if self.mode == 'dash': return
        
		# add stuff to the bottom toolbar
		button = gtk.Button()
		button.set_label('About Melia')
		im = gtk.Image()
		im.set_from_file('melia_logo_r2-64.png')
		button.set_image(im)
		button.set_image_position(gtk.POS_TOP)
		button.connect('clicked', self.show_about_dialog)
		self.ui.bottom_toolbar.append_widget(button, 'About Melia', 'AbouuutMleiea')
		self.ui.bottom_toolbar.show_all()
    
   
    def show_about_dialog(self, widget, data=None):
        d = self.parent.AboutDialog()
        d.run()
        d.destroy()
    
    def search(self, widget, data=None):
        self.query = widget.get_text()
        
        self.sparql_query = """
                    SELECT ?uri ?mime
                    WHERE { 
                        ?item a nie:InformationElement;
                            nie:url ?uri;
                            nie:mimeType ?mime;
                            tracker:available true.
                            FILTER (fn:contains(fn:lower-case(?uri), "%s"))
                          }
                    ORDER BY ASC(?uri)
                    LIMIT %d
                """ 
        self.tracker.SparqlQuery(self.sparql_query % (self.query, 50),
            dbus_interface='org.freedesktop.Tracker1.Resources',
            reply_handler=self.prepare_and_handle_search_result,
            error_handler=self.handle_search_error
            )
            
	def prepare_and_handle_search_result(self, results):

		formatted_results = []	
		
		for pr in self.parent.launcher_index:
		    if self.query.lower() in pr[0].lower(): formatted_results.append({'name': pr[0], 'icon': pr[1], 'path': pr[2]})

		for result in results:
			
			dummy, canonical_path = splittype(result[0])
			parent_name, child_name = split(canonical_path)
			icon_name = result[1]

			formatted_result = {
				'name'         : child_name,
				'icon'    : icon_name,
				'tooltip'      : result[0],
				'path'      : canonical_path,
				'type'         : 'xdg',
				'context menu' : None,
				}

			formatted_results.append(formatted_result)

		#if results:
	#		formatted_results.append(self.action)
	    self.handle_results(formatted_results)

		
		
    def handle_search_error(self, error):
        logger.warn('Tracker search error: ' + error)
        
    def handle_results(self, results):
        # empty the table
        for button in self.default_buttons: button.hide()
        
        for button in self.current_buttons: button.destroy()
        self.current_buttons = []
        # row and column indices for calculating where to attach each button
        col = 0
        row = 0
        for res in results:
            #if self.query.lower() not in res['path'].lower(): 
            # create the button
            btn = gtk.Button()
            # create the image
            img = gtk.Image()
            self.current_buttons += [btn]
            
            # two methods: (1) check if it is a .desktop file and grab the icon from that. (2) try to guess from the mimetype
            if res['icon'] == 'application/x-desktop' and res['name'].endswith('.desktop'):
                cf = ConfigParser()
                cf.read(res['name'])
                items = cf.items('Desktop Entry')
                name, swc, command, icon = False, False, False, False
                for c in items:
                    if c[0] == 'name': name = c[1]
                    elif c[0] == 'icon': icon = c[1]
                    elif c[0] == 'exec': command = c[1].replace('%U', '').replace('%u', '')
                if icon and name and command:
                    img.set_from_icon_name(icon, gtk.ICON_SIZE_DIALOG)
                    btn.set_label(name)
                    btn.set_image(img)
                    btn.set_image_position(gtk.POS_TOP)
                    btn.command = command
                    
            else: 
                btn.set_label(res['name'])
                btn.set_tooltip_text(res['path'])
                btn.command = res['path']
                if res['icon'].startswith('image/'):
                    try: 
                        img.set_from_file(res['path'].replace('///', '/'))
                        btn.set_image(img)
                        btn.set_image_position(gtk.POS_TOP)
                    except: logger.warn('Failed to load image: %s' % res['path'].replace('///', '/'))
                else:
                    img.set_from_icon_name(res['icon'].replace('/', '-'), gtk.ICON_SIZE_DIALOG)
                    btn.set_image(img)
                    btn.set_image_position(gtk.POS_TOP)
                    
            btn.set_size_request(128, 128) 
            btn.set_relief(gtk.RELIEF_HALF)
            img.set_size_request(48, 48) 
            img.set_pixel_size(48)  
            btn.connect('clicked', self.open_file)       
            self.ui.table3.attach(btn, col, col+1, row, row+1)
            col += 1
            if col == 4: 
                row += 1
                col = 0
            btn.show()
           
                    
    def open_file(self, widget, data=None):
        if not os.path.exists(widget.command.replace('///', '/')): 
            logger.warn('Attempt to open file %s failed, as it does not exist. attempting to run it as a command' % widget.command.replace('///', '/'))
            subprocess.call(widget.command.split())
            return
        logger.debug("running 'xdg-open %s'" % widget.command)
        os.system('xdg-open %s' % widget.command)
    def on_key(self, widget, data):
        if data.keyval == 65307:
            self.ui.entry1.set_text('')
            for button in self.default_buttons: button.show()
            
            for button in self.current_buttons: button.destroy()
            self.current_buttons = []

            if self.mode == 'dash': self.hide()


if __name__ == "__main__":
    dialog = MeliaDashboardDialog()
    dialog.show()
    gtk.main()
    
    
