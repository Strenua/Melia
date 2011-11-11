#####################################################################
#                                                                   #
# This file contains the core application logic for the Melia shell #
#                                                                   #
#####################################################################

import wnck
import clutter
screen = wnck.screen_get_default()

# a dictionary of xid-to-button
open_windows = {}

def add_window(emitter, window, panel=None):
    '''Add a taskbar button for a window, or add a window to a group'''
    if not panel: panel = emitter
    if not window.get_window_type().value_nick == "normal" or not window.is_on_workspace(screen.get_active_workspace()) or window.is_skip_tasklist(): return
    
        
    pixbuf = window.get_icon()
    print pixbuf
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
    
    panel.taskbox.append(button)
    open_windows.update({window.get_xid(): button})
    
def remove_window(emitter, window, panel):
    xid = window.get_xid()
    if xid not in open_windows.keys(): return
    button = open_windows[xid]
    panel.taskbox.remove(button)
    open_windows.pop(xid)
    
def on_taskbutton_click(panel, button):
    '''Handle button press events for the taskbar buttons'''
