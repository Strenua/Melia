import os
import gtk
import gobject


class Indicator(gtk.ImageMenuItem):
    '''A class for Melia indicator applets'''
    _submenu = None
    
    def __init__(self, icon=None, menu=None):
        '''Initialize a Melia indicator applet'''
        gtk.ImageMenuItem.__init__(self, '')
        if icon: self.set_image(gtk.image_new_from_icon_name(icon))
        self.finit()
        
    def finit(self):
        return
    
    def set_icon(self, icon):
        self.img = gtk.Image()
        self.img.set_from_icon_name(icon, gtk.ICON_SIZE_BUTTON)
        self.set_image(self.img)
        
    def set_menu(self, menu):
        self._submenu = menu
        self.set_submenu(menu)
        
    def open_submenu(self, widget):
        if not self._submenu:
            raise NameError('No menu specified for %s indicator! Please use Indicator.set_submenu(menu)' % self.__name__)
            return
        #if not self.get_state() == gtk.STATE_ACTIVE: self.set_state(gtk.STATE_ACTIVE)
        self._submenu.popup(None, None, self.get_submenu_position, 0, gtk.get_current_event_time())
        self._submenu.button = widget
        #self.activate()
        win = self.get_toplevel()
        win.active_indicator = self._submenu
        
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
        
        
