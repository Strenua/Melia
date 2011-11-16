#!/usr/bin/env python
import sys
import clutter
import gtk
from clutter import x11
import wnck
import glib

from lib import logic
import mtk

button = gtk.Button()

screen = wnck.screen_get_default()
# make wnck events, and other events non-blocking
while gtk.events_pending():
    gtk.main_iteration()

class CairoGradientActor(clutter.CairoTexture):
    def __init__(self):
        super(CairoGradientActor, self).__init__(32, screen.get_height())
        self.connect('draw', self.on_draw)
        
    def on_draw(self, a=None, b=None):
        print 'DRAW', a, b

class HelloClutter:
    orientation = mtk.ORIENTATION_VERTICAL
    strict = False
    def __init__ (self):
        self.stage = clutter.Stage()
        self.stage.set_color(clutter.color_from_string('#222'))
        self.stage.set_use_alpha(True)
        self.stage.set_size(32, 738)
        self.stage.set_position(0, 28)
        self.stage.set_title('Melia Shell')
        self.stage.connect('destroy', clutter.main_quit)
        
        self.taskbox = mtk.Container(self.orientation, 0)
        
        for win in screen.get_windows():
            logic.add_window(self, win)
        screen.connect('window-opened', logic.add_window, self)
        screen.connect('window-closed', logic.remove_window, self)

        #mybutton = mtk.Button(icon='midori', size=(32,60), flat=True)
        #mybutton.connect('clicked', self.on_midori_clicked)
        #box.append(mybutton)
        
        self.stage.add(self.taskbox)
        
    def on_midori_clicked(self, btn, event):
        if event.button == 3: 
            m = mtk.Menu()
            px, py = btn.get_position()
            sx, sy = btn.get_size()
            mx = px + sx
            my = py + sy
            print mx, my
            m.set_position(mx, 0)
            m.append(mtk.Button(icon='nautilus', size=(m.get_size()[0], 30), flat=True))
            m.show_all()
            
    def create_taskbutton(self, label='', icon='help'):
        if self.orientation == mtk.ORIENTATION_VERTICAL: label = None
        #if type(icon) != str: 
        #    if self.strict: raise TypeError
        #    else: icon = None
        try: button = mtk.Button(icon=icon, size=(32,60), flat=True, label=label, labelpos='right')
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
