# This is the system indicator (for lock-screen, log out, shut down, etc)
# Feel free to use this as an example for creating your own indicators!
import gtk
from melia_lib import indicator

class SystemIndicator(indicator.Indicator):
    def __init__(self):
        indicator.Indicator.__init__(self, 'firefox')
        menu = gtk.Menu()
        item1 = gtk.MenuItem('Lock Screen')
        menu.append(item1)
        menu.append(gtk.SeparatorMenuItem())
        menu.show_all()
        self.set_menu(menu)
        
if __name__ == '__main__':
    SystemIndicator()
