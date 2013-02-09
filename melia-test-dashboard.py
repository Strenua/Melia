#!/usr/bin/env python
import clutter
import mtk
import wnck
import os
from clutter import x11
import time
from lib import logic

screen = wnck.screen_get_default()

SCREEN_WIDTH, SCREEN_HEIGHT = (screen.get_width(), screen.get_height())

content_width = 0.7*SCREEN_WIDTH
if content_width < 600: content_width = 600
if content_width > SCREEN_WIDTH: content_width = SCREEN_WIDTH
padding_width = (SCREEN_WIDTH-content_width)/2
print content_width

x11.set_use_argb_visual(True)
        
app_list = logic.index_applications()

class Dashboard(mtk.Stage):
    def __init__(self):
        clutter.init()
        super(Dashboard, self).__init__()
        
        self.connect('destroy', clutter.main_quit)
        self.connect('show', self.make_me_fullscreen)
        self.connect('key-release-event', self.keyrelease)
        
        color = clutter.Color(0x00, 0x00, 0x00, 0xaa)
        self.set_color(color)
        self.set_use_alpha(True)
        
        vbox = mtk.Container(mtk.ORIENTATION_VERTICAL)

        searchbox = mtk.Entry(content_width, 25)
        vbox.append(searchbox)
        
        appbox = mtk.Container(mtk.ORIENTATION_VERTICAL)
        dragaction = clutter.DragAction()
        dragaction.set_drag_axis(clutter.DRAG_Y_AXIS)
        appbox.add_action(dragaction)
        appbox.set_reactive(True)
    
        appbox.set_position(padding_width, searchbox.get_size()[1])
        appbox.start_pos = appbox.get_position()
        appbox.connect('scroll-event', self.on_scroll)
        dragaction.connect('drag-end', self.finish_drag)
        dragaction.connect('drag-begin', self.start_drag)
        self.add(appbox)

        hbox = mtk.Container(mtk.ORIENTATION_HORIZONTAL, spacing=6)
        appbox.append(hbox)
        count = 0
        for app in app_list: 
            if count >= (content_width - ((content_width/73)-2)*6)/73 - 1:
                hbox = mtk.Container(mtk.ORIENTATION_HORIZONTAL, spacing=6)
                appbox.append(hbox)
                count = 0
            if app[2]: testbutton = mtk.Button(label=app[0], icon=app[2], size=(73, 73), flat=True, labelpos='bottom', iconsize=48, background_color='#000', hover_color='#555a')
            testbutton.app = app
            testbutton.connect('clicked', self.launcher_down)
            testbutton.connect('button-release-event', self.launch)
            hbox.append(testbutton)
            count += 1
        
        vbox.set_position(padding_width, 0)
        self.add(vbox)
        
        ### filter buttons ###
        cvbox = mtk.Container(mtk.ORIENTATION_VERTICAL, spacing=4)
        
        logic.default_categories.insert(0, 'All')
        for category in logic.default_categories:
            cb = mtk.Button(label=category, icon=logic.category_icons[category], labelpos='right', background_color='#000', flat=True, size=(200,32), hover_color='#555a')
            cvbox.append(cb)
            
        self.add(cvbox)
        cvbox.set_position(0, (self.get_size()[1]/2) - (cvbox.get_size()[1]/2))
        self.clicked_at = (0,0)
        self.dragged = False
                
    def make_me_fullscreen(self, actor, event=None):
        self.set_fullscreen(True)
        
    def run (self):
        self.show_all()
        clutter.main()
    
    def launcher_down(self, actor, event=None):
        now = time.localtime()
        self.clicked_at = (now.tm_min/60) + now.tm_sec
    
    def launch(self, actor, event=None):
        now = time.localtime()
        if self.dragged: return
        print ((now.tm_min/60) + now.tm_sec) - self.clicked_at >= 3
        if ((now.tm_min/60) + now.tm_sec) - self.clicked_at >= 3: 
            self.held(actor, event)
            return
        
        print 'running', actor.app[1].replace('%u', '').replace('%U', '')
        clutter.main_quit()
        os.system(actor.app[1].replace('%u', '').replace('%U', '') + ' &')
        
    def keyrelease(self, actor, event=None):
        if event.keyval == 65307: clutter.main_quit()

    def start_drag(self, action, actor, event_x, event_y, modifiers, data=None):
        self.started_at = (event_x, event_y)

    def finish_drag(self, action, actor, event_x, event_y, modifiers, data=None):
        print event_x, event_y, self.started_at
        if (event_x, event_y) == self.started_at: self.dragged = False
        else: self.dragged = True
        if actor.get_position()[1] > actor.start_pos[1]: actor.animate(clutter.LINEAR, 200, 'y', actor.start_pos[1])
        elif actor.get_position()[1] < actor.start_pos[1]-actor.get_size()[1]+SCREEN_HEIGHT-actor.start_pos[1]: 
            actor.animate(clutter.LINEAR, 200, 'y', actor.start_pos[1]-actor.get_size()[1]+SCREEN_HEIGHT-actor.start_pos[1])
            
    def on_scroll(self, actor, event, data=None):
        amount = 0
        if event.direction == clutter.SCROLL_UP: amount = 73
        elif event.direction == clutter.SCROLL_DOWN: amount = -73
        if (actor.get_position()[1] <= actor.start_pos[1] and actor.start_pos[1] - actor.get_position()[1] >= 73 and amount > 0) or (actor.get_position()[1] > actor.start_pos[1]-actor.get_size()[1]+SCREEN_HEIGHT-actor.start_pos[1] and amount < 0): actor.animate(clutter.LINEAR, 50, 'y', actor.get_position()[1] + amount)
        elif actor.get_position()[1] <= actor.start_pos[1] and actor.start_pos[1] - actor.get_position()[1] < 73 and amount > 0: actor.animate(clutter.LINEAR, 50, 'y', actor.start_pos[1])
                
d = Dashboard()
d.run()
