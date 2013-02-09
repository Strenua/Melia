#!/usr/bin/env python
import sys
import mtk
import clutter, gtk
from clutter import x11
#from gi.repository import Clutter, GtkClutter, Gtk

button = gtk.Button()

x11.set_use_argb_visual(True)
clutter.init()

class HelloClutter(mtk.Stage):
    def __init__ (self):
        super(HelloClutter, self).__init__()

        self.set_user_resizable(False)
        self.set_size(800, 600)
        self.set_title('Melia Test App')

        self.connect('destroy', clutter.main_quit)

        color = clutter.Color(0x00, 0x00, 0x00, 0xaa)
        self.set_color(color)
        self.set_use_alpha(True)

        self.layout = mtk.Container(mtk.ORIENTATION_VERTICAL)
        self.add(self.layout)

        self.populate()

    def populate(self):
        hboxen = [mtk.Container(mtk.ORIENTATION_HORIZONTAL) for i in range(2)]
        for button in [mtk.Button(label='Button %d' % i, flat=True) for i in range(5)]:
            hboxen[0].append(button)
        entry = mtk.Entry(200, 20, placeholder="Input")
        hboxen[1].append(entry)
        for hbox in hboxen: self.layout.append(hbox)
                        
    def run (self):
        self.show_all()
        clutter.main()
        

def main (args):
    app = HelloClutter()
    app.run()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
