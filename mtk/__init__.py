# -*- coding: utf8 -*-
import clutter, gtk
import cairo
from config import Config

CONFIG = Config()['mtk']

_button = gtk.Button()

import gobject

ORIENTATION_VERTICAL, ORIENTATION_HORIZONTAL = range(2)


class Container(clutter.Box):
    '''A container which automatically arranges widgets, so they never overlap
    Also allows scrolling, when necessary'''
    def __init__(self, orientation, spacing=2):
        self.layout = clutter.BoxLayout()
        self.layout.set_use_animations(True)
        if orientation == ORIENTATION_VERTICAL: self.layout.set_vertical(True)
        self.layout.set_spacing(spacing)

        super(Container, self).__init__(self.layout)
        
        self.orientation = orientation
        self.spacing = spacing
        
        self.contents = []

        # x and y positions of the edge of the last widget added, used for placing the next widget
        self.lastx = 0
        self.lasty = 0
        
    
    def layout(self, actor, startpos=None):
        if not startpos: startpos = (self.lastx, self.lasty)
        if self.orientation == 0: x, y = (0, self.lasty + self.spacing)
        else: x, y = (self.lastx + self.spacing, 0)
        self.lastx, self.lasty = x + actor.get_size()[0], y + actor.get_size()[1]
        actor.set_position(x, y)
        
    def append(self, actor):
        '''Append a widget to the container, automatically positioning it relative to other widgets in the container'''
        #self.add(actor)
        #actor.first = True
        #actor.connect('queue-relayout', self.relayout)
        #self.contents.append(actor)
        #self.layout(actor)
        self.layout.pack(actor, False, False, False, clutter.BOX_ALIGNMENT_START, clutter.BOX_ALIGNMENT_START)
        
    def relayout(self, actor):
        if not actor.first: self.layout(actor, actor.get_position())
        else: actor.first = False
    
    def remove(self, actor):
        if self.lastx: self.lastx -= actor.get_width()
        if self.lasty: self.lasty -= actor.get_height()
        if self.contents.index(actor) < len(self.contents)-1: 
            for c in self.contents[self.contents.index(actor)+1:]:
                x,y = actor.get_position()
                c.set_position(x, y)
                
        self.contents.pop(self.contents.index(actor))
        
        actor.destroy()
        
class Texture(clutter.Texture):
	def set_from_icon_name(self, name, size):
		icontheme = gtk.icon_theme_get_default()
		pixbuf = icontheme.load_icon(name, size, 0)
		if pixbuf.props.has_alpha: a = 4
		else: a = 3
		self.set_from_rgb_data(
			pixbuf.get_pixels(),
			pixbuf.props.has_alpha,
			pixbuf.props.width,
			pixbuf.props.height,
			pixbuf.props.rowstride,
			a,
			0
		)	
        
class Button(clutter.Group):
    classname = 'Button'
    def __init__(self, label=None, icon=None, size=(100, 30), pos=(0, 0), labelpos='bottom', flat=False, graddirection=(0.0, 0.0, 0.0, 1.0), iconsize=None, background_color=None, hover_color=None):
        super(Button, self).__init__()
        self.icon_name = icon
        self.label_text = label
        self.size = size
        self.pos = pos
        self.flat = flat
        self.graddirection = graddirection
        self.iconsize = iconsize
        self.background_color = background_color
        self.hover_color = hover_color
        
      # set default buttonish behaviour
        
        # bind buttonish events
        self.set_reactive(True)
        self.connect('button-press-event', self.on_click_btn)
        self.connect('button-release-event', self.on_release_btn)
        self.connect('enter-event', self.on_enter)
        self.connect('leave-event', self.on_leave)
        
        # configure
        self.set_size(size[0], size[1])
        self.set_position(pos[0], pos[1])
        
        #self.button.set_color(clutter.color_from_string('#222'))
        
        if not flat: 
            self.button = clutter.CairoTexture(width=size[0], height=size[1])
            ctx = self.button.cairo_create()
            ctx.scale(size[0], size[1])
            pat = cairo.LinearGradient (graddirection[0], graddirection[1], graddirection[2], graddirection[3])
            pat.add_color_stop_rgba(1, 0.1, 0.1, 0.1, 1)
            pat.add_color_stop_rgba(0, 0.3, 0.3, 0.3, 1)
            
            ctx.rectangle (0,0,1,1)
            ctx.set_source (pat)
            ctx.fill ()
            
            del(ctx)
            
    #        self.button.set_border_width(2)
     #       self.button.set_border_
     #color(clutter.color_from_string('#212121'))
      #      self.button.set_color(clutter.color_from_string('#333'))
       #     self.color = '#333'
        else: 
            self.button = clutter.Rectangle()
            self.set_state('normal')
            self.lastbtncolor = self.button.get_color()
        
        bs = clutter.BindConstraint(self, clutter.BIND_WIDTH, -100)
        #self.button.add_constraint(bs)
        
        self.button.set_size(size[0], size[1])
        self.add(self.button)
        
        
        if icon: 
            if size[0] > size[1] and not self.iconsize: self.iconsize = size[1]
            elif not self.iconsize: self.iconsize = size[0]
        	
            if type(icon) == str or type(icon) == unicode:
                self.icon = Texture()
                try: self.icon.set_from_icon_name(icon, self.iconsize)
                except: 
                    self.icon = None
                    self.icon_name = None
                    icon = None
            else: self.icon = icon            
                    
        if icon: # ask again in case it was just dropped    
            self.icon.set_size(self.iconsize, self.iconsize)
            
            # find the center of the button for the icon
            if self.icon_name: icenterx = (self.get_size()[0]/2) - (self.icon.get_size()[0]/2)
            if self.icon_name: icentery = (self.get_size()[1]/2) - (self.icon.get_size()[1]/2)
            
            # and center the icon if there isn't a label
            if self.icon_name and not self.label_text: self.icon.set_position(icenterx, icentery)
            
            self.add(self.icon)
            
        if label: 
            self.label = clutter.Text()
            self.label.set_text(label)
            
            # compute the necessary resizies
            x, y = self.get_size()
            lx, ly = self.label.get_size()
            shortened = False

            while lx + 21 > x:
                shortened = True
                self.label.set_text(self.label.get_text()[:-1])
                lx = self.label.get_size()[0]

            if shortened: self.label.set_text(self.label.get_text().strip()+'…')
            if labelpos == 'bottom' and self.icon_name or labelpos == 'top' and self.icon_name: y += ly
            elif labelpos == 'left' and self.icon_name or labelpos == 'right' and self.icon_name: x += lx
            if self.size == (80, 30): # skip if the size has been set manually
                self.set_size(x, y)
                self.button.set_size(x, y)
            
            # find the center of the button for the label
            centerx = (self.get_size()[0]/2) - (self.label.get_size()[0]/2)
            centery = (self.get_size()[1]/2) - (self.label.get_size()[1]/2)
            
                                    
            # move the label wherever it goes
            x, y = self.get_size()
            #print centerx, centery
            if icon and labelpos == 'bottom': self.label.set_position(centerx, y - self.label.get_size()[1])
            elif icon and labelpos == 'top': self.label.set_position(centerx, 0) # just center it
            elif icon and labelpos == 'right' and self.icon_name: self.label.set_position(self.icon.get_size()[0] + 10, centery)
            elif not icon: self.label.set_position(int(centerx), int(centery)) # center both ways
            
            # move the icon wherever *it* goes
            if labelpos == 'top' and self.icon_name: self.icon.set_position((self.get_size()[0]/2)-(self.icon.get_size()[0]/2), self.label.get_size()[1])
            elif labelpos == 'bottom' and self.icon_name: self.icon.set_position((self.get_size()[0]/2)-(self.icon.get_size()[0]/2), 0)

            # label color
            self.label.set_color(CONFIG['button']['color'])
            self.add(self.label)

            # make sure the label isn't too wide, and if it is, shorten the label.
            lx, ly = self.label.get_size()
            bx, by = self.get_size()
            if lx + 2 > bx:
                self.label.set_max_length(10)
                # and move it over to the new center
                bpx, bpy = self.get_position()
                lpx, lpy = self.label.get_position()
                self.label.set_position(bpx + (self.get_size()[0]/2) - (self.label.get_size()[0]/2), lpy)
                #if labelpos == 'right': self.label.set_position(self.label.get_position()[0] + self.icon.get_size()[0] + 10, lpy)
                
            self.label.raise_top()
        
        # set up the simple color transition animation
        anim = clutter.Animation()
        anim.set_object(self.button)
        anim.set_duration(500)
        
    
    def set_icon_by_name(self, name):
        if icon: self.icon.set_from_icon_name(_button, icon)

    def set_state(self, state):
        '''Set the state of the button. 
        State can be one of 'normal', 'down', or 'highlight' '''
        if self.flat: 
            self.lastbtncolor = self.button.get_color()
            self.button.animate(clutter.LINEAR, 50, 'color', clutter.color_from_string(self.background_color or CONFIG['button'][state]['background-color'][0] if state == 'normal' else self.hover_color or CONFIG['button'][state]['background-color'][0]))
        else: 
            ctx = self.button.cairo_create()
            ctx.scale(self.size[0], self.size[1])
            graddirection = self.graddirection
            pat = cairo.LinearGradient(graddirection[0], graddirection[1], graddirection[2], graddirection[3])
            col1 = clutter.color_from_string(CONFIG['button'][state]['background-color'][0])
            col2 = clutter.color_from_string(CONFIG['button'][state]['background-color'][1])

            pat.add_color_stop_rgba(0 if state == 'down' else 1, round(col1.red/255.0,2), round(col1.blue/255.0,2), round(col1.green/255.0,2), round(col1.alpha/255.0,2))
            pat.add_color_stop_rgba(1 if state == 'down' else 0, round(col2.red/255.0,2), round(col2.blue/255.0,2), round(col2.green/255.0,2), round(col2.alpha/255.0,2))
                                                                       
            ctx.rectangle(0,0,1,1)
            ctx.set_source(pat)
            ctx.fill()
            del(ctx)
            del(pat)
            del(col1)
            del(col2)
            self._state = state
              
    def on_click_btn(self, btn, event):
        self.set_state('down') 
        self.emit('clicked', event)
        
    def on_release_btn(self, btn, event):
        self.set_state('hover')
        
    def on_enter(self, w, event):
        self.set_state('hover')
        
    def on_leave(self, w, event):
        self.set_state('normal')
        
gobject.type_register(Button)
gobject.signal_new("clicked", Button, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))
gobject.property("color", clutter.Color(0xff,0xff,0xff,0xff))

class Stage(clutter.Stage):
    def __init__(self, *args, **kwargs):
        super(Stage, self).__init__(*args, **kwargs)
        self.connect('destroy', clutter.main_quit)
        self.set_reactive(True)
        self.set_color(clutter.color_from_string(CONFIG['stage']['background-color']))
        self.add_action(clutter.DragAction())
                   
class Menu(clutter.Stage):
    '''A menu. To be used with tap-hold/right-click and MtkMenuButton'''
    def __init__(self, *args, **kwargs):
        super(Menu, self).__init__(*args, **kwargs)
        bg = clutter.Rectangle()
        self.add(bg)
        self.items = 0
        self.itemheight = 30
        self.set_size(80, 30)
        
    def append(self, item):
        '''Append a MtkButton to the menu'''
        self.add(item)
        item.set_position(0, self.itemheight * self.items)
        item.set_size(self.get_size()[0], self.itemheight)
        self.items += 1
        self.set_size(80, self.itemheight * self.items)
        
    def activate(self, x, y):
        self.show()
        self.move(x, y)
       
gobject.type_register(Menu)
gobject.signal_new("activated", Menu, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())       
            
class MenuButton(Button):
    '''A widget derived from MtkButton specialized for activating an MtkMenu when clicked'''
    def __init__(self, *args, **kwargs):    
        super(MenuButton, self).__init__(*args, **kwargs)

        
#gobject.type_register(Button)


class Entry(clutter.Box):
    def __init__(self, width, height, placeholder=""):
        super(Entry, self).__init__(clutter.BoxLayout())

        # create cluttertext
        self.text = clutter.Text()
        self.text.set_text(placeholder)
        self.add(self.text)
        
        # function
        self.text.set_editable(True)
        self.text.set_cursor_color(clutter.color_from_string("#000"))
        self.text.set_cursor_visible(True)
        
        self.set_reactive(True)
        
        # style
        self.set_color(clutter.color_from_string("#fff"))        
        self.text.set_color(clutter.color_from_string("#000"))
        
        self.set_size(width, height)
        
        # other stuff
        self.connect('button-press-event', self.on_focus)
        #self.text.set_text('Text')
        
        
    def on_focus(self, actor, data=None):
        self.get_stage().set_key_focus(self.text)
        
gobject.type_register(Entry)
