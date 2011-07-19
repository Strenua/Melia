# This is the system indicator (for lock-screen, log out, shut down, etc)
# Feel free to use this as an example for creating your own indicators!
import gtk
import time, datetime
from melia_lib import indicator

class menu(indicator.Indicator):
    def finit(self):
        menu = gtk.Menu()
        self.dt = self.construct_and_append(menu, ['Date, Time [loading...]'])
        self.set_label('date time')
        self.update_time()
        gtk.timeout_add(1000, self.update_time)

        menu.show_all()
        self.set_menu(menu)
        #self.set_icon('system-shutdown')
    def update_time(self):
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Nov', 'Dec']
        sdtf = ' %d %H:%M'
        sdt = time.strftime(sdtf)
        month = months[datetime.datetime.now().month - 1]
        sdt = month + sdt
        self.set_label(str(sdt))
        
        weeks = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ldt = weeks[int(time.strftime('%w')) - 1] + time.strftime(', %d ') + month + ' ' + str(datetime.datetime.now().year)
        self.dt[0].set_label(str(ldt))
        return True
        
