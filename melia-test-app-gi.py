#!/usr/bin/env python
import sys
import mtk
from gi.repository import Clutter, ClutterX11, Gtk

button = Gtk.Button()

class HelloClutter:
    def __init__ (self):
        self.stage = Clutter.Stage()
        color = Clutter.Color()
        #self.stage.set_color(Clutter.color_from_string('#000'))
        self.stage.set_use_alpha(True)
        self.stage.set_color(color)
#        self.stage.set_user_resizable(False)
#        self.stage.set_size(800, 600)
#        self.stage.set_title('My First Clutter Application')
        self.stage.connect('destroy', Clutter.main_quit)
        
        vbox = mtk.Container(mtk.ORIENTATION_VERTICAL)
        #vbox.set_position(2,2)
        self.stage.add_actor(vbox)
        
        box0 = mtk.Container(mtk.ORIENTATION_HORIZONTAL)
        button0 = mtk.Button(label='Button')
        box0.append(button0)
        
        button1 = mtk.Button(icon='help')
        box0.append(button1)
        
        button2 = mtk.Button(icon='help', label='Button With Icon', labelpos='right')
        box0.append(button2)
        
        vbox.append(box0)
        
        box1 = mtk.Container(mtk.ORIENTATION_HORIZONTAL)
        button3 = mtk.Button(label='Flat Button', flat=True)
        box1.append(button3)
        
        button4 = mtk.Button(icon='help', flat=True)
        box1.append(button4)
        
        button5 = mtk.Button(icon='help', label='Button With Icon', labelpos='right', flat=True)
        box1.append(button5)
        
        vbox.append(box1)
                
    def run (self):
        self.stage.show_all()
        ClutterX11.set_use_argb_visual(True)
        Clutter.init(('Melia Test App', 'something'))
        Clutter.main()

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
