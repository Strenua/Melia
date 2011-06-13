import dbus, dbus.service, gobject, threading
from dbus.mainloop.glib import DBusGMainLoop
from dbus.service import method, signal
window = None

# start dbus main loop
DBusGMainLoop(set_as_default=True)

# set some dbus options
DBUS_BUSNAME = "org.dosprompt.DOSprompt"
DBUS_IFACE = 'org.dosprompt.DOSpromptSync'
DBUS_PATH = '/org/dosprompt/DOSprompt/PluginSync'

class MeliaObject(dbus.service.Object):

    @method(dbus_interface=DBUS_IFACE, in_signature="")
    def update_qls(self):
        print 'Instructed via DBus to update quicklists. Doing it!'
        window.update_qls()




session_bus = dbus.SessionBus()
busname = dbus.service.BusName(DBUS_BUSNAME, bus=session_bus)
eo = MeliaObject(object_path=DBUS_PATH, bus_name=busname)
#loop = gobject.MainLoop()
#######################################################################

def start_loop(wind0w):
    window = wind0w
    #loop.run()
    
def stop_loop():
    loop.quit()
