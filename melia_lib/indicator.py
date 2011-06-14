import os
import gtk
import gobject

def calculate_screen_pos(window_pos, window_size):
    x = window_pos[0] + window_size[0]
    y = window_pos[1] + window_size[1]
    return x, y    

def set_indicator_menu_pos(menu, data=None):
    print menu, data
    return (1290, 25, True)
    
class Indicator(gtk.ToggleButton):
    '''A class for Melia indicator applets'''
    
    def __init__(self, icon='no-icon', menu=None):
        '''Initialize a Melia indicator applet'''
        gtk.ToggleButton.__init__(self)
        self.img = gtk.Image()
        self.img.set_from_icon_name(icon, gtk.ICON_SIZE_BUTTON)
        self.set_image(self.img)
        self.set_relief(gtk.RELIEF_NONE)
        
    def set_menu(self, menu):
        self._menu = menu
        self.connect('toggled', self.open_menu)
        
    def open_menu(self):
        if not menu: raise TypeError('No menu specified for %s indicator! Please use Indicator.set_menu(menu)' % self.__name__)
        self._menu.popup(None, None, self.get_position, 0, gtk.get_current_event_time())
        self._menu.button = widget
        self._menu.connect('deactivate', self.indicator_untoggle)
        
    def get_position(self):
        '''Return a three-tuple of the screen coordinates of the Indicator's button, and True'''
        return calculate_screen_pos(self.get_position(), self.get_size(), True)
        
    def append_to_stack(self):
        '''Run this when you are done creating your indicator to actually add it to the indicator area'''
      #  os.system("dbus-send --print-reply --dest=org.strenua.Melia /org/strenua/Melia/MeliaIF org.strenua.Melia.MeliaIF.load_indicator string:'%s'" % __name__)

