#!/usr/bin/env python
import sys
import clutter
import cluttergtk
import gtk
from clutter import x11
import wnck


import mtk

button = gtk.Button()
       
       
screen = wnck.screen_get_default()

class CairoGradientActor(clutter.CairoTexture):
    def __init__(self):
        super(CairoGradientActor, self).__init__(32, screen.get_height())
        self.connect('draw', self.on_draw)
        
    def on_draw(self, a=None, b=None):
        print 'DRAW', a, b

class HelloClutter:
    def __init__ (self):
        self.stage = clutter.Stage()
        self.stage.set_color(clutter.color_from_string('#222'))
        self.stage.set_use_alpha(True)
        self.stage.set_user_resizable(False)
        self.stage.set_size(32, 738)
        self.stage.set_position(0, 0)
        self.stage.set_title('Melia\'s Bar')
        self.stage.connect('destroy', clutter.main_quit)

        # setup the gradient background
        grad = CairoGradientActor()

        #grad.set_surface_size(int(self.stage.get_size()[0]), int(self.stage.get_size()[1]))
        #grad.invalidate()
        #self.stage.add(grad)

        box = mtk.Container(mtk.CONTAINER_VERTICAL, 0)

        mybutton = mtk.Button(icon='midori', size=(32,60), flat=True)
        mybutton.connect('clicked', self.on_midori_clicked)
        box.append(mybutton)
        
        mybutton = mtk.Button(icon='leafpad', size=(32,60), flat=True)
        box.append(mybutton)
        
        self.stage.add(box)
        
        t = cluttergtk.Texture()
        t.set_from_icon_name(button, 'nm-signal-75')
        t.set_size(32, 32)
        t.set_position(0, 700)
        self.stage.add(t)
        
        t = cluttergtk.Texture()
        t.set_from_icon_name(button, 'battery_plugged')
        t.set_size(32, 32)
        t.set_position(0, 700 - 32)
        self.stage.add(t)
    
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
        
    def run (self):
        self.stage.show_all()
        clutter.main()

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
