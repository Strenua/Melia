import clutter, gtk

_button = gtk.Button()

import gobject

ORIENTATION_VERTICAL, ORIENTATION_HORIZONTAL = range(2)

class Container(clutter.Group):
    '''A container which automatically arranges widgets, so they never overlap
    Also allows scrolling, when necessary'''
    def __init__(self, orientation, spacing=2):
        super(Container, self).__init__()
        
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
        self.add(actor)
        actor.first = True
        #actor.connect('queue-relayout', self.relayout)
        self.contents.append(actor)
        self.layout(actor)
        
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
		pixbuf = icontheme.load_icon(name, size, gtk.ICON_LOOKUP_USE_BUILTIN)
		self.set_from_rgb_data(
			pixbuf.get_pixels(),
			pixbuf.props.has_alpha,
			pixbuf.props.width,
			pixbuf.props.height,
			pixbuf.props.rowstride,
			4,
			0
		)	
        
class Button(clutter.Group):
    def __init__(self, label=None, icon=None, size=(80, 30), pos=(0, 0), labelpos='bottom', flat=False):    
        super(Button, self).__init__()
        self.icon_name = icon
        self.label_text = label
        self.size = size
        self.pos = pos
        self.flat = flat
        
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
        
        # add actors
        
        #self.button.set_color(clutter.color_from_string('#222'))
        self.color = '#222'
        
        if not flat: 
            self.button = clutter.Texture('button-normal.png')
    #        self.button.set_border_width(2)
     #       self.button.set_border_color(clutter.color_from_string('#212121'))
      #      self.button.set_color(clutter.color_from_string('#333'))
       #     self.color = '#333'
        else: 
            self.button = clutter.Rectangle()
            self.button.set_color(clutter.color_from_string('#222'))
            self.lastbtncolor = self.button.get_color()
        
        bs = clutter.BindConstraint(self, clutter.BIND_WIDTH, -100)
        #self.button.add_constraint(bs)
            
        self.button.set_size(size[0], size[1])
        self.add(self.button)
        
        
        if icon: 
            if size[0] > size[1]: self.iconsize = size[1]
            else: self.iconsize = size[0]
        	
            if type(icon) == str:
                self.icon = Texture()
                self.icon.set_from_icon_name(icon, self.iconsize)
                
            else: self.icon = icon            
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
            if labelpos == 'bottom' and self.icon_name or labelpos == 'top' and self.icon_name: y += self.label.get_size()[1]
            elif labelpos == 'left' and self.icon_name or labelpos == 'right' and self.icon_name: x += self.label.get_size()[0]
            self.set_size(x, y)
            self.button.set_size(x, y)
            
            # find the center of the button for the label
            centerx = (self.get_size()[0]/2) - (self.label.get_size()[0]/2)
            centery = (self.get_size()[1]/2) - (self.label.get_size()[1]/2)
            
                                    
            # move the label wherever it goes
            if labelpos == 'bottom': self.label.set_position(centerx, y - self.label.get_size()[1])
            elif labelpos == 'top': self.label.set_position(centerx, 0) # just center it
            elif labelpos == 'right' and self.icon_name: self.label.set_position(self.icon.get_size()[0] + 10, centery)
            if not icon: self.label.set_position(centerx, centery) # center both ways
            
            # move the icon wherever *it* goes
            if labelpos == 'top' and self.icon_name: self.icon.set_position(0, self.label.get_size()[1])            

            # label color
            self.label.set_color(clutter.color_from_string('#fff'))
            self.add(self.label)

            # make sure the label isn't too wide, and if it is, resize the button.
            lx, ly = self.label.get_size()
            bx, by = self.get_size()
            if lx + 2 > bx:
                self.set_size(lx + 2, by)
                self.button.set_size(lx + 2, by)
                # and move it over to the new center
                bpx, bpy = self.get_position()
                lpx, lpy = self.label.get_position()
                self.label.set_position(bpx + (self.get_size()[0]/2) - (self.label.get_size()[0]/2), lpy)
                #if labelpos == 'right': self.label.set_position(self.label.get_position()[0] + self.icon.get_size()[0] + 10, lpy)
            
        # set up the simple color transition animation
        anim = clutter.Animation()
        anim.set_object(self.button)
        anim.set_duration(500)
        
    
    def set_icon_by_name(self, name):
        if icon: self.icon.set_from_icon_name(_button, icon)
              
    def on_click_btn(self, btn, event):
        if self.flat: 
            self.lastbtncolor = self.button.get_color()
            self.button.animate(clutter.LINEAR, 50, 'color', clutter.color_from_string('#333'))
        else: self.button.set_from_file('button-active.png')
            
        self.emit('clicked', event)
        
    def on_release_btn(self, btn, event):
        if self.flat: self.button.set_color(self.lastbtncolor)
        else: self.button.set_from_file('button-normal.png')
        
    def on_enter(self, w, event):
        if self.flat: self.button.animate(clutter.LINEAR, 150, 'color', clutter.color_from_string('#555'))
        else: self.button.set_from_file('button-prelight.png')
        
        
    def on_leave(self, w, event):
        if self.flat: self.button.animate(clutter.LINEAR, 150, 'color', clutter.color_from_string(self.color))
        else: self.button.set_from_file('button-normal.png')
        
gobject.type_register(Button)
gobject.signal_new("clicked", Button, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_PYOBJECT,))

class Stage(clutter.Stage):
    def __init__(self, *args, **kwargs):
        super(Stage, self).__init__(*args, **kwargs)
        self.connect('destroy', clutter.main_quit)
        self.set_color(clutter.color_from_string('#000'))
                   
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
