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
        button = mtk.Button(label='Button')
        self.stage.add(button)

        button1 = mtk.Button(icon='help')
        button1.set_position(82, 0)
        self.stage.add(button1)

        button2 = mtk.Button(icon='help', label='Button With Label', labelpos='right')
        button2.set_position(164, 0)
        self.stage.add(button2)
        
                
    def run (self):
        self.stage.show_all()
        clutter.main()

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
