# This is the system indicator (for lock-screen, log out, shut down, etc)
# Feel free to use this as an example for creating your own indicators!
import gtk
import os
from melia_lib import indicator

class button(indicator.Indicator):
    def finit(self):
        menu = gtk.Menu()
        ls, s0, gs, sf, s1, lo, sus, res, sd = self.construct_and_append(menu, ['Lock Screen', gtk.SeparatorMenuItem(), 'Guest Session', 'Switch From %s...' % os.getenv('LOGNAME'), gtk.SeparatorMenuItem(), 'Log Out...', 'Suspend', 'Restart...', 'Shut Down...'])

        menu.show_all()
        self.set_menu(menu)
        self.set_icon('system-shutdown')
        
