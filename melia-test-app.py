#!/usr/bin/env python
import sys
import mtk
import clutter, gtk
from clutter import x11
#from gi.repository import Clutter, GtkClutter, Gtk

button = gtk.Button()

x11.set_use_argb_visual(True)

class HelloClutter:
    def __init__ (self):
        clutter.init()
        self.stage = clutter.Stage()
        color = clutter.Color(0x00, 0x00, 0x00, 0xaa)
        self.stage.set_color(color)
        self.stage.set_user_resizable(False)
        self.stage.set_size(800, 600)
        self.stage.set_title('Melia Test App')
        self.stage.connect('destroy', clutter.main_quit)
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

        # text entry row
        entry1 = mtk.Entry(200, 20)
        entry1.text.set_text("blah")
        entry1.connect('button-press-event', self.entry_focused)
        
        vbox.append(entry1)
                        
    def run (self):
        self.stage.show_all()
        clutter.main()
        
    def entry_focused(self, actor, data):
        self.stage.set_key_focus(actor.text)

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
