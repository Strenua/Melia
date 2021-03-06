import mtk
import clutter
import sys, os
from Xlib import display, Xatom, Xutil
import virtkey, time
v = virtkey.virtkey()

display = display.Display()
root = display.screen().root

##### TODO XXX TODO #####
# The only thing that prevents this from truly working is that it steals focus from the window it's trying to type in :(
# To avoid that, it needs some X11 properties set. That is... not easy.
# First, gotta get the window's XID. ... Okay, just go with that for now.

def get_window_by_title(title):
    for outside in root.query_tree().children:
        if outside.get_wm_name() == title:
            return outside
        for inside in outside.query_tree().children:
            if inside.get_wm_name() == title:
                return inside
    return None


class KBWin(mtk.Stage):
    def __init__(self):
        clutter.init()
        super(KBWin, self).__init__()
        self.container = mtk.Container(mtk.ORIENTATION_VERTICAL)
        self.add(self.container)
        
        self.set_size(800, 200)
        self.set_property('accept-focus', False)
        
        self.connect('activate', self.set_props)
        
        self.keys = (
                         [('q/^Q',113,81), ('w/^W',119,87), ('e/^E',101,69), ('r/^R',114,82), ('t/^T',116,84), ('y/^Y',121,89), ('u/^U',117,85), ('i/^I',105,73), ('o/^O',111,79), ('p/^P',112,80), ('icon:edit-clear',22)],
                         [('a/^A',97,65), ('s/^S',115,83), ('d/^D',100,68), ('f/^F',102,70), ('g/^G',103,71), ('h/^H',104,72), ('j/^J',106,74), ('k/^K',107,75), ('l/^L',108,76), ('size:98,48;return',36)],
                         [('z/^Z',122,90), ('x/^X',120,88), ('c/^C',99,67), ('v/^V',118,86), ('b/^B',98,66), ('n/^N',110,78), ('m/^M',109,77), (',/^<',59), ('./^>',60), ('//^?',61)],
                       )
        for row in self.keys:
            rowbox = mtk.Container(mtk.ORIENTATION_HORIZONTAL)
            for l in row:
                if l[0].startswith('size:'): 
                    size = (int(l[0].split(':')[1].split(';')[0].split(',')[0]), int(l[0].split(':')[1].split(';')[0].split(',')[1]))
                    l = (l[0].split(';')[1], l[1:])
                else: size = (48, 48)
                if l[0].startswith('icon:'): button = mtk.Button(flat=True, icon=':'.join(l[0].split(':')[1:]), size=size)
                else: button = mtk.Button(flat=True, label=l[0].split('/^')[0], size=size)
                button.rowbox = rowbox
                button.l = l
                button.connect('clicked', self.key_press)
                rowbox.append(button)
                
            self.container.append(rowbox)
                
    def key_press(self, button, event):
        print 'Key', chr(button.l[1]), 'pressed.'
        v.press_unicode(button.l[1]), v.release_unicode(button.l[1])

    def set_props(self, e):
        win = get_window_by_title('melia-osk.py')
        win.change_property(display.intern_atom("_NET_WM_WINDOW_TYPE"), Xatom.ATOM, 32, [display.intern_atom("_NET_WM_WINDOW_TYPE_DOCK")])
        win.set_wm_hints(flags=(Xutil.InputHint|Xutil.StateHint), input=0, initial_state=1)
        


    def run (self):
        self.show_all()
        clutter.main()
        
                    
def main (args):
    app = KBWin()
    app.run()
    return 0
                                
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
