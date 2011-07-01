import os
import gtk
import gobject


class Indicator(gtk.ToggleButton):
    '''A class for Melia indicator applets'''
    _menu = None
    
    def __init__(self, icon=None, menu=None):
        '''Initialize a Melia indicator applet'''
        gtk.ToggleButton.__init__(self)
        if icon: self.set_icon(icon)
        self.set_relief(gtk.RELIEF_NONE)
        
    def finit(self):
        return
    
    def set_icon(self, icon):
        self.img = gtk.Image()
        self.img.set_from_icon_name(icon, gtk.ICON_SIZE_BUTTON)
        self.set_image(self.img)
        
    def set_menu(self, menu):
        self._menu = menu
        self.connect('toggled', self.open_menu)
        self._menu.connect('deactivate', self.indicator_untoggle)
        
    def open_menu(self, widget):
        if not self._menu:
            raise NameError('No menu specified for %s indicator! Please use Indicator.set_menu(menu)' % self.__name__)
            return
        #if not self.get_state() == gtk.STATE_ACTIVE: self.set_state(gtk.STATE_ACTIVE)
        self._menu.popup(None, None, self.get_menu_position, 0, gtk.get_current_event_time())
        self._menu.button = widget
        #self.activate()
        win = self.get_toplevel()
        win.active_indicator = self._menu
        
    def indicator_untoggle(self, widget):
        self._menu.hide()
        if not self.get_state() == gtk.STATE_NORMAL: self.set_state(gtk.STATE_NORMAL)
        win = self.get_toplevel()
        win.active_indicator = None
        
    def get_menu_position(self, w=None):
        '''Return a three-tuple of the screen coordinates of the Indicator's button, and True'''
        tl = self.get_toplevel()
        indicators = tl.indicators[::-1]
        x, y = self.calculate_screen_pos(tl.get_position(), tl.get_size(), indicators)
        return x, y, True
        
    def construct_and_append(self, menu, items):
        '''Take a list of strs, create menu items from them, and return the items'''
        out = []
        for label in items:
            if type(label) == gtk.SeparatorMenuItem: menu.append(label)
            else:
                item = gtk.MenuItem(label)
                menu.append(item)
            out += [item]
        return out
        

    def calculate_screen_pos(self, window_pos, window_size, indicators):
        x = (window_pos[0] + window_size[0]) - (indicators.index(self) * 102)
        x -= 102
        y = (window_pos[1] + window_size[1]) + 1
        print x, y
        return x, y   
        
        
