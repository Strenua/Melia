#####################################################################
#                                                                   #
# This file contains the core application logic for the Melia shell #
#                                                                   #
#####################################################################

import wnck
import gtk
import clutter
from xdg import DesktopEntry
import os
screen = wnck.screen_get_default()

# a dictionary of xid-to-button
open_windows = {}

# and class name to button
groups = {}

def add_window(emitter, window, panel=None, data={}):
    '''Add a taskbar button for a window, or add a window to a group'''
    if not panel: panel = emitter
    if not window.get_window_type().value_nick == "normal" or window.is_skip_tasklist(): return
    if not data.get('all_workspaces') and not window.is_on_workspace(screen.get_active_workspace()): return
    
    print window.get_name()
    
    pixbuf = window.get_icon()
    if window.get_icon_is_fallback():
        pixbuf = gtk.gdk.pixbuf_new_from_file('window.png')
    icon = clutter.Texture()
    icon.set_from_rgb_data(
        pixbuf.get_pixels(),
        pixbuf.props.has_alpha,
        pixbuf.props.width,
        pixbuf.props.height,
        pixbuf.props.rowstride,
        4,
        0
    )

    
    button = panel.create_taskbutton(window.get_class_group().get_name(), icon)
    button.appname = window.get_name()
    button.window = window
    
    if window.get_class_group().get_name() in groups.keys() and data.get('group_windows'):
        # use the existing button, and add an indicator that there are more windows
        button = groups.get(window.get_class_group().get_name())
    else: 
        groups.update({window.get_class_group().get_name(): button})
        panel.taskbox.append(button)
        
    open_windows.update({window.get_xid(): button})

    
def remove_window(emitter, window, panel):
    xid = window.get_xid()
    if xid not in open_windows.keys(): return
    button = open_windows[xid]
    button.destroy()
    open_windows.pop(xid)
    
def on_taskbutton_click(button, event):
    '''Handle button press events for the taskbar buttons'''
    win = button.window
    if not win.is_minimized() and win.is_active():
        win.minimize()
    elif not win.is_minimized() and not win.is_active():
        win.activate(gtk.get_current_event_time())
    else: win.unminimize(gtk.get_current_event_time())
    
    
    
# for the dashboard
default_categories = ["AudioVideo", "Audio", "Video", "Development", "Education", "Game", "Graphics", "Network", "Office", "Settings", "System", "Utility"]
category_icons = {
        "All": "",
        "AudioVideo": 'applications-multimedia',
        "Audio": 'applications-multimedia',
        "Video": 'applications-multimedia',
        "Development": 'applications-development',
        "Education": 'applications-science',
        "Game": 'applications-games',
        "Graphics": 'applications-graphics',
        "Network": 'applications-internet',
        "Office": 'applications-office',
        "Settings": 'applications-engineering',
        "System": 'applications-system',
        "Utility": 'applications-other',
}

def index_applications():
    out = []
    apps = []
    #return [('Test', 'test', 'help', '/usr/share/applications/firefox.desktop')]
    for dr in [d.rstrip('/')+'/applications/' for d in os.getenv('XDG_DATA_DIRS').split(':')]:
        for d in os.listdir(dr):
            try: 
                desktop = DesktopEntry.DesktopEntry(dr+d)
                if desktop.getName() not in apps and desktop.getIcon() and not 'wine' in desktop.getExec(): out += [(desktop.getName(), desktop.getExec(), desktop.getIcon(), desktop.getFileName())]
                apps += [desktop.getName()]
            except: pass
    del(apps)
    out.sort()
    return out
    
def find_apps(query, index):
    out = []
    for item in index:
        if query.lower() in item[0].lower() or query.lower() in item[1].lower() or query.lower() in item[2].lower(): out += [item]
    return out
