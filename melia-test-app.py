#!/usr/bin/env python
import sys
import mtk
import clutter, cluttergtk, gtk
#from gi.repository import Clutter, GtkClutter, Gtk

button = gtk.Button()

class HelloClutter:
    def __init__ (self):
        self.stage = clutter.Stage()
        self.stage.set_color(clutter.color_from_string('#000'))
        #self.stage.set_property('alpha', 0)
        self.stage.set_user_resizable(False)
        self.stage.set_size(800, 600)
        self.stage.set_title('My First Clutter Application')
        self.stage.connect('destroy', clutter.main_quit)
        self.stage.set_opacity(0)
        self.stage.set_use_alpha(True)
        
        vbox = mtk.Container(mtk.ORIENTATION_VERTICAL)
        #vbox.set_position(2,2)
        self.stage.add(vbox)
        
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
        clutter.main()

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
