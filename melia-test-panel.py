#!/usr/bin/env python
import sys
import clutter
import gtk
from clutter import x11
import wnck
import glib
import cairo
import math

from lib import logic
import mtk

button = gtk.Button()

screen = wnck.screen_get_default()

SCREEN_WIDTH, SCREEN_HEIGHT = (screen.get_width(), screen.get_height())

#### Temporary Configuration #############################
position = (0, 0) # x, y coords of this panel
size = (32, SCREEN_HEIGHT) # x, y dimensions of this panel (variables that can be used are SCREEN_WIDTH and SCREEN_HEIGHT)
all_workspaces = True # show and manipulate windows from all workspaces?
group_windows = False

##########################################################

# make wnck events, and other events non-blocking
while gtk.events_pending():
    gtk.main_iteration()

class GradientStage(clutter.Stage):
    def __init__(self):
        super(GradientStage, self).__init__()
        gradient = clutter.CairoTexture(width=32, height=screen.get_height())
        gradient.set_position(0, 0)
        
        ctx = gradient.cairo_create()
        ctx.scale(32, screen.get_height())
        pat = cairo.LinearGradient (0.0, 0.0, 1.0, 0.0)
        pat.add_color_stop_rgba(1, 0.1, 0.1, 0.1, 1)
        pat.add_color_stop_rgba(0, 0.3, 0.3, 0.3, 1)

        ctx.rectangle (0,0,1,1)
        ctx.set_source (pat)
        ctx.fill ()

        del(ctx)
        
        self.add(gradient)
        gradient.show()
        
        #self.connect('draw', self.on_draw)
        
    def on_draw(self, a=None, b=None):
        print 'DRAW', a, b

class HelloClutter:
    orientation = mtk.ORIENTATION_VERTICAL
    strict = False
    def __init__ (self):
        clutter.init()
        self.stage = GradientStage()
        self.stage.set_color(clutter.color_from_string('#222'))
        self.stage.set_use_alpha(True)
        self.stage.set_size(size[0], size[1])
        self.stage.set_position(position[0], position[1])
        self.stage.set_title('Melia Shell')
        self.stage.connect('destroy', clutter.main_quit)
        
        self.taskbox = mtk.Container(self.orientation, 0)
        
        for win in screen.get_windows():
            logic.add_window(self, win, data={'all_workspaces': all_workspaces, 'group_windows': group_windows})
        screen.connect('window-opened', logic.add_window, self)
        screen.connect('window-closed', logic.remove_window, self)

        #mybutton = mtk.Button(icon='midori', size=(32,60), flat=True)
        #mybutton.connect('clicked', self.on_midori_clicked)
        #box.append(mybutton)
        
        self.stage.add(self.taskbox)
        
    def create_taskbutton(self, label='', icon='help'):
        if self.orientation == mtk.ORIENTATION_VERTICAL: label = None
        #if type(icon) != str: 
        #    if self.strict: raise TypeError
        #    else: icon = None
        try: button = mtk.Button(icon=icon, size=(32,60), label=label, labelpos='right', graddirection=(0.0, 0.0, 1.0, 0.0))
        except glib.GError: button = mtk.Button(icon='help', size=(32,60), flat=True, label=label, labelpos='right')
        button.connect('clicked', logic.on_taskbutton_click)
        return button
        
    def run (self):
        self.stage.show_all()
        clutter.main()

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
