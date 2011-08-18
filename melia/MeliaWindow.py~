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

import gtk, wnck, webkit

#class MeliaWebkitFrame(webkit.WebFrame):
#    def finish_initializing(self):
#        ''

class BrowserPage(webkit.WebView):

    def __init__(self):
        webkit.WebView.__init__(self)
        settings = self.get_settings()
        settings.set_property("enable-developer-extras", False)

        # scale other content besides from text as well
        self.set_full_content_zoom(True)

        # make sure the items will be added in the end
        # hence the reason for the connect_after
        #self.connect_after("populate-popup", self.populate_popup)


        
class MeliaWindow(gtk.Window):
    def finish_initializing(self):
        main = BrowserPage()

        self.add(main)
        
        # set up the frame
        #main.open('file:///home/mike/git/Melia/main.html')
                
        main_vars = {
          'data_dir': 'file://' + os.getcwd(),
        }
        
        f = open('main.html')
        main_html = f.read()
        for s in main_html.split('{{ ')[1:]:
            s = s.split(' }}')[0]
            print '{{ %s }}' % s, str(main_vars.get(s))
            main_html = main_html.replace('{{ %s }}' % s, str(main_vars.get(s)))
        f.close()

        main.load_uri('file:///home/mike/git/Melia/main.html')
        
        if 'window' not in sys.argv: self.fullscreen()
        else: self.maximize()
        
        im = gtk.Image()
        im.set_from_icon_name('start-here', gtk.ICON_SIZE_BUTTON)
        print #im.get_icon_set()
        
        self.show_all()
        if 'shoot' in sys.argv: gtk.timeout_add(1000, self.screenshot)
        
    def screenshot(self):
        os.system('gnome-screenshot &')


