import dbus, dbus.service, gobject, threading
from dbus.mainloop.glib import DBusGMainLoop
from dbus.service import method, signal
import gtk
import random

global window
window = None
def init(wind0w):
    global window
    window = wind0w
    
    
# start dbus main loop

# set some dbus options
DBUS_BUSNAME = "org.strenua.Melia"
DBUS_IFACE = 'org.strenua.Melia.MeliaIF'
DBUS_PATH = '/org/strenua/Melia/MeliaIF'

class MeliaObject(dbus.service.Object):

    @method(dbus_interface=DBUS_IFACE, in_signature="")
    def update_qls(self):
        print 'Instructed via DBus to update quicklists. Doing it!'
        window.update_qls()

    #@method(dbus_interface=DBUS_IFACE, in_signature="s")
    #def load_indicator(self, indicator):
    #    print 'Instructed via DBus to add an indicator. Doing it!'
    #    window.panel.load_indicator(indicator)






DBUS_BUSNAME = "org.freedesktop.Notifications"
DBUS_IFACE = 'org.freedesktop.Notifications'
DBUS_PATH = '/org/freedesktop/Notifications'

class NotificationObject(dbus.service.Object):

    def show_notification(self, icon, summary, body, timeout):
        print 'about to construct a notification dialog'
        md = gtk.MessageDialog(None, gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_INFO, gtk.BUTTONS_CLOSE, summary)
        md.run()
        md.destroy()

    @method(dbus_interface=DBUS_IFACE, in_signature="")
    def GetCapabilities(self):
        return [u'body',
                #u'body-markup',
                u'icon-static',
                u'image/svg+xml',
                #u'x-strenua-icon-glow',
                #u'x-canonical-private-synchronous',
                u'x-canonical-append',
                #u'x-canonical-private-icon-only',
                #u'x-canonical-truncation',
                #u'private-synchronous',
                u'append',
                #u'private-icon-only',
                #u'truncation'
                ]
    @method(dbus_interface=DBUS_IFACE, in_signature="")
    def GetServerInformation(self):
        return (u'melia-notify', u'Strenua', u'1.0', u'1.1')
        
    @method(dbus_interface=DBUS_IFACE, in_signature="susssasa{sv}i")
    def Notify(self, app_name, id, icon, summary, body, actions, hints, timeout):
        global window
        if not id: id = random.randint(100, 10000)
        print '%s is sending a notification!' % app_name
        if window: window.show_notification(id, icon, summary, body, timeout)
        else: 
            print 'ERROR! COULD NOT FIND WINDOW!'
            self.show_notification(icon, summary, body, timeout)
        return id
        

#loop = gobject.MainLoop()
#######################################################################

def run():
    DBusGMainLoop(set_as_default=True)
    DBUS_BUSNAME = "org.strenua.Melia"
    DBUS_IFACE = 'org.strenua.Melia.MeliaIF'
    DBUS_PATH = '/org/strenua/Melia/MeliaIF'
    session_bus0 = dbus.SessionBus()
    busname0 = dbus.service.BusName(DBUS_BUSNAME, bus=session_bus0)
    eo0 = MeliaObject(object_path=DBUS_PATH, bus_name=busname0)
    DBUS_BUSNAME = "org.freedesktop.Notifications"
    DBUS_IFACE = 'org.freedesktop.Notifications'
    DBUS_PATH = '/org/freedesktop/Notifications'
    session_bus1 = dbus.SessionBus()
    busname1 = dbus.service.BusName(DBUS_BUSNAME, bus=session_bus1)
    eo1 = NotificationObject(object_path=DBUS_PATH, bus_name=busname1)

#run()
    
def stop_loop():
    loop.quit()
