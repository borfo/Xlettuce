#!/usr/bin/python3

# xprobe - miscellaneous classes for gathering information about the user's X environment

import subprocess, Xlib, Xlib.display, re, weakref
import logging
logger = logging.getLogger(__name__)

class Bunch( dict ):
    #simple object class that allows adding arbitrary attributes, also readable as dict
    def __init__(self,**kw):
        dict.__init__(self,kw)
        self.__dict__ = self


class Screen:
    '''
    Gathers information about the user's X screen/monitor geometry.
    '''
    
    def __init__( self, parent ):
        #initialize xlib objects
        self.parent = weakref.proxy(parent)
        self.display = Xlib.display.Display()
        self.root = self.display.screen().root
        
        self.refresh() # get screen geometry info

        
    def refresh( self ):
        '''Check screen geometry
        Call on init, and whenever screen changes or changes to the config file are detected.
        '''
        
        # probe for screen information
        self.probe_screen()
        # retrieve info about connected monitors
        self.probe_monitors()

    
    def probe_screen( self ):
        """
        Determine screen layout, panel clearances, etc.  Calculate tiling area for each active monitor.
        Called on init, should also be called on screen geometry change.
        """
        
        # pull full screen size and per-monitor info from xrandr
        self.xrandr=subprocess.check_output("xrandr", universal_newlines=True)

        #initialize monitor Bunch - stores screen geometry and geometry for all monitors
        self.monitor = Bunch()
        self.monitor.count=0
        
        #get screen info from xrandr
        match=re.search("^Screen 0:[ \w,]*current ([0-9]*) x ([0-9]*)", self.xrandr, flags=re.MULTILINE)
        # ------match groups: (0:width) (1:height)
        self.width = int(match.group(1))
        self.height = int(match.group(2))

        # get workarea size - this doesn't include the panels - # returns a list at workarea.value[] composed of ints [ x, y, width, height ] for each available virtual desktop
        workarea = self.root.get_full_property(self.display.intern_atom('_NET_WORKAREA'), Xlib.X.AnyPropertyType) 
        
        self.avail_width = int(workarea.value[2]) # tiling area width (px)
        self.avail_height = int(workarea.value[3]) # tiling area height (px)
        self.avail_screenX = int(workarea.value[0]) # tiling area offset from screen origin
        self.avail_screenY = int(workarea.value[1]) # tiling area offset from screen origin        
        
        # calculate panel size on all four edges - this assumes there isn't a panel on middle edges of multimonitor setup
        self.panel_left = int(self.avail_screenX)
        self.panel_right = self.width - ( self.avail_screenX + self.avail_width )
        self.panel_top = self.avail_screenY
        self.panel_bottom = self.height - ( self.avail_screenY + self.avail_height )


    def probe_monitors( self ):
        '''retrieve monitor information for up to four connected monitors.'''
        
        # check for PRIMARY monitor
        match=re.search("^([-A-Z0-9]*) connected primary ([0-9]*)x([0-9]*)\+([0-9]*)\+([0-9]*)", self.xrandr, flags=re.MULTILINE)
        # ------match groups: (0:device_name) (1:width) (2:height) (3:xpos) (4:ypos)
        if ( match ):
            # there is a primary monitor.  Initialize [0] and get its info
            self.monitor[0] = self.probe_monitor_geometry( 0, match )
            
            # make alias for primary
            self.monitor[ 'primary' ] = self.monitor[ 0 ]
            self.monitor['count'] += 1 # monitor counter

        # gather info on all other connected monitors
        for match in re.finditer( "^([-A-Z0-9]*) connected ([0-9]*)x([0-9]*)\+([0-9]*)\+([0-9]*)", self.xrandr, flags=re.MULTILINE ):
            # ------match groups: (0:device_name) (1:width) (2:height) (3:xpos) (4:ypos)
            
            self.monitor[self.monitor['count']] = self.probe_monitor_geometry( self.monitor['count'], match )
            self.monitor['count'] += 1 # increment monitor count
            
            if ( self.monitor['count'] >= 4 ) :
                break # only supports 4 monitors for now - artificial limitation though, because conf file only specifies 4 monitor grids, 4 activation buttons, etc.  TODO: fix this limitation - practically speaking it's probably fine, but may as well fix.


    def probe_monitor_geometry( self, monitornum, regex_match ):
        '''
        Parse a regex match to pull monitor geometry information
        eg: HDMI-0 connected primary 3840x2160+0+0
        ------match groups: (0:device_name) (1:width) (2:height) (3:xpos) (4:ypos)
        '''
        mon=Bunch()
        mon.workarea=Bunch()
        mon.lattice=Bunch()
        
        mon.name = str( regex_match.group(1) )
        mon.width = int( regex_match.group(2) ) # monitor width in Pixels
        mon.height = int( regex_match.group(3) ) # monitor height in Pixels
        mon.screenX = int( regex_match.group(4) ) # X Offset of monitor relative to whole screen
        mon.screenY = int( regex_match.group(5) ) # Y Offset of monitor relative to whole screen
        
        # calculate active workarea - ie: the tiling area - space accessible to windows, excludes inaccessible areas covered by panels, etc.
        # this assumes no panels in the middle of multimonitor setups
        #TODO: make this calculation more robust - calculate based on a maximized window? 
        mon.workarea.screenX = max( self.avail_screenX, mon.screenX ) # X coordinate of this monitor's work area relative to the whole screen
        mon.workarea.screenY = max( self.avail_screenY, mon.screenY ) # Y coordinate of this monitor's work area relative to the whole screen
        mon.workarea.monX = mon.workarea.screenX - mon.screenX # work area X offset relative to monitor
        mon.workarea.monY = mon.workarea.screenY - mon.screenY # work area Y offset relative to monitor
        mon.workarea.width = ( mon.width - mon.workarea.monX ) - max ( 0, ( mon.screenX + mon.width - (self.avail_screenX + self.avail_width ) ) )
        mon.workarea.height = ( mon.height - mon.workarea.monY ) - max ( 0, ( mon.screenY + mon.height - (self.avail_screenY + self.avail_height ) ) )
        
        # create tiling grid
        mon.lattice.gridX = int( self.parent.conf.get("MONITORS", "Mon"+str( monitornum )+'_Grid_X' ) ) # number of grid hotkeys - pulls from conf
        mon.lattice.gridY = int( self.parent.conf.get("MONITORS", "Mon"+str( monitornum )+'_Grid_Y' ) ) # number of grid hotkeys - pulls from conf
        mon.lattice.slotsX = mon.lattice.gridX # number of lattice slots - one less than the number of grid keys
        mon.lattice.slotsY = mon.lattice.gridY # number of lattice slots - one less than the number of grid keys
        mon.lattice.slotWidth = mon.workarea.width // mon.lattice.gridX
        mon.lattice.slotHeight = mon.workarea.height // mon.lattice.gridY
        
        return mon


    def set_grab_trigger( self, keycode = 66 ):
        '''Sets up the root object to capture presses and releases of a specific trigger key.
        Generates all possible mod key combinations for the trigger key.
        Keycode should be the value labeled "Keycode" in the output of the xev bash command.
        Defaults to 66 -> CAPS_LOCK 
        Trigger key will activate XLettuce when pressed, and deactivate it when released.
        '''
        self.root.change_attributes( event_mask = Xlib.X.KeyPressMask | Xlib.X.KeyReleaseMask )
        for v in range(256):
            # generate and grab all possible mod key combinations for capslock key.
            self.root.grab_key(66, v, 1, Xlib.X.GrabModeAsync, Xlib.X.GrabModeAsync)
                
    def grab_keyboard( self ):
        self.root.grab_keyboard(1, Xlib.X.GrabModeAsync, Xlib.X.GrabModeAsync,  Xlib.X.CurrentTime)


    def ungrab_keyboard( self ):
        self.display.ungrab_keyboard(Xlib.X.CurrentTime)


    def set_num_desktops( self, num=9 ):
        '''set the number of virtual desktops.  Defaults to recommended 9 for good 3x3 grid navigation.'''
        self.send_event( self.root, self.display.intern_atom("_NET_NUMBER_OF_DESKTOPS"), [num] )


    def get_active_window( self ):
        '''Finds the active window, probes for window information, and returns a window object
        '''
        activewindowID = self.root.get_full_property(self.display.intern_atom('_NET_ACTIVE_WINDOW'), Xlib.X.AnyPropertyType).value[0]
        self.activeWindow = self.display.create_resource_object('window', activewindowID)
        self.activeWindow.info=self.get_xwininfo(self.activeWindow)
        return self.activeWindow;
    
                
    def get_xwininfo( self,  window ):
        geom = window.get_geometry()
        info={
        "x": geom.x,
        "y": geom.y,
        "width": geom.width,
        "height": geom.height,
        "root": geom.root,
        'fullheight': 0,
        'fullwidth': 0,
        'border': 0,
        'padleft': 0,
        'padtop': 0,
        'padright': 0,
        'padbottom': 0,
        'container': 0,
        'containergeom': 0 }

        try:
            info["WM_NAME"]=window.get_full_property(39, Xlib.X.AnyPropertyType).value
        except ( AttributeError, TypeError ):
            info["WM_NAME"]=False
        try:
            info["WM_CLASS"]=window.get_full_property(67, Xlib.X.AnyPropertyType).value
        except ( AttributeError, TypeError ):
            info["WM_CLASS"]=False
        try:
            info["WM_NORMAL_HINTS"]=window.get_full_property(40, Xlib.X.AnyPropertyType).value
        except ( AttributeError, TypeError ):
            info["WM_NORMAL_HINTS"]=False
        try:
            info["WM_HINTS"]=window.get_full_property(35, Xlib.X.AnyPropertyType).value
        except ( AttributeError, TypeError ):
            info["WM_HINTS"]=False

        info['fullheight']=geom.height+(2*geom.border_width) # height of active window including border
        info['fullwidth']=geom.width+(2*geom.border_width) # width of active window including border
        info['border']=geom.border_width # width of the active window border
        info['padleft']=geom.x # offset from the container window
        info['padtop']=geom.y # offset from the container window
        info['container']=window
        info['containergeom']=geom

        curwin=window.query_tree().parent

        while ( curwin !=  self.root):
            geom=curwin.get_geometry()
            info['padright'] += ( geom.width - ( info['fullwidth'] + info['padleft'] ) )
            info['padbottom'] += ( geom.height - ( info['fullheight'] + info['padtop'] ) )
            if (curwin.query_tree().parent != self.root):
                info['padleft']+=geom.x
                info['padtop']+=geom.y
            info['container']=curwin
            info['containergeom']=geom
            curwin=curwin.query_tree().parent

        return info


    def get_current_monitor( self , event ):
        #set current monitor
        for i in range (0, self.monitor['count']):
            minX=self.monitor[i].screenX
            maxX=self.monitor[i].screenX+self.monitor[i].width
            minY=self.monitor[i].screenY
            maxY=self.monitor[i].screenY+self.monitor[i].height

            if ( event.root_x >= minX and event.root_x <= maxX and event.root_y >= minY and event.root_y <= maxY):
                self.currentMonitor=i
                break
        
        return self.currentMonitor


    def send_event( self, win, ctype, data, mask=None ):
        """ Send a ClientMessage event to the root window """
        data = (data+[0]*(5-len(data)))[:5]
        ev = Xlib.protocol.event.ClientMessage(window=win, client_type=ctype, data=(32,(data)))

        if not mask:
            mask = (Xlib.X.SubstructureRedirectMask|Xlib.X.SubstructureNotifyMask)

        self.root.send_event(ev, event_mask=mask)
        self.display.flush()


        
class KeyEvent:
    '''
    Tools to gather information about Xorg Keypress Events
    '''
    
    def __init__( self, event, parent ):
        self.parent = weakref.proxy(parent)
        self.event = event;
        self.action = self.keycode = self.is_keypress = self.is_keyrelease = self.is_mapping_notify = False
        
        if ( event.type == Xlib.X.MappingNotify ):
            self.is_mapping_notify = True
        elif ( event.type == Xlib.X.KeyPress ):
            self.is_keypress = True
            self.keycode = event.detail
        elif ( event.type == Xlib.X.KeyRelease ):
            self.is_keyrelease = True
            self.keycode = event.detail
        else:
            # it's some other type of event.  What's up?  Log it.
            logger.warning("####################################\n")
            logger.warning("####################################\n WEIRD EVENT: %s" % ( event.type ) )
            logger.warning("%s \n\n" % ( str(event ) ) )
            logger.warning("dir: %s" % ( str(dir(event) ) ) )
            logger.warning("####################################\n")
            logger.warning("####################################\n")
            logger.warning("####################################\n")
            
        
    def get_mods( self ):
        #get modifiers
        self.modshift=(self.event.state & Xlib.X.ShiftMask) >> Xlib.X.ShiftMapIndex
        self.modcontrol=(self.event.state & Xlib.X.ControlMask) >> Xlib.X.ControlMapIndex
        self.modalt=(self.event.state & 0b1000) >> 3
        self.modsuper=(self.event.state & 0b1000000) >> 6
        if ( self.modshift + self.modsuper + self.modcontrol + self.modalt == 0 ):
            self.modnone = 1
        else:
            self.modnone = 0

    def modonly(self, modname):
        """test whether the specified keyboard modifier is the only modifier"""
        if (modname == "shift") and self.modshift and not (self.modcontrol | self.modalt | self.modsuper):
            return True
        elif (modname == "control") and self.modcontrol and not (self.modshift | self.modalt | self.modsuper):
            return True
        elif (modname == "alt") and self.modalt and not (self.modcontrol | self.modshift | self.modsuper):
            return True
        elif (modname == "super") and self.modsuper and not (self.modcontrol | self.modalt | self.modshift):
            return True
        else:
            return False


    
    def log_key_event( self ):
        logger.debug("event.type: %s | event.detail: %s | event.state: %s | event.root_x %s | event.root_y %s | self.modnone: %s | self.modalt: %s | self.modshift: %s | self.modcontrol: %s | self.modsuper: %s" % ( self.event.type, self.event.detail, format(self.event.state, '08b'), self.event.root_x, self.event.root_y, self.modnone, self.modalt, self.modshift, self.modcontrol, self.modsuper ) )
        
    def get_action( self ):
        '''Determine if key event is an action hotkey'''
        
        if ( self.is_keypress and self.keycode == self.parent.trigger_keycode and self.parent.isActive == False ):
            self.action = "trigger_press";
        
        elif ( self.is_keyrelease and self.keycode == self.parent.trigger_keycode and self.parent.isActive == True ):
            self.action = "trigger_release"
        
        elif ( self.is_keypress == False ) or ( self.parent.isActive == False ) :
            # None of the remaining hotkeys have these properties, so exit.
            self.action = False
            return False
        
        elif ( self.keycode == self.parent.conf.get("MONITORS", "Mon0_Hotkey") ):
            self.action = "set_monitor_0"

        elif ( self.keycode == self.parent.conf.get("MONITORS", "Mon1_Hotkey") ):
            self.action = "set_monitor_1"

        elif ( self.keycode == self.parent.conf.get("MONITORS", "Mon2_Hotkey") ):
            self.action = "set_monitor_2"

        elif ( self.keycode == self.parent.conf.get("MONITORS", "Mon3_Hotkey") ):
            self.action = "set_monitor_3"
        
        elif ( ( self.modnone or self.modonly("shift") ) and self.keycode in self.parent.tilekeymap and self.parent.activeWindow != self.parent.root and ( str(self.parent.activeWindow.info['WM_NAME']).lower() !=  "desktop" ) ):
            self.action = "tilekey"
            
        elif ( self.keycode in self.parent.desktopkeymap ):
            self.action = "desktopkey"
            
        elif ( self.modnone and self.keycode in self.parent.cursorkeys and self.parent.valid_window() ):
            self.action = "movewin"
            
        elif ( self.modonly("shift") and self.keycode in self.parent.cursorkeys and self.parent.valid_window() ):
            self.action = "sizewin_tl"
            
        elif ( self.modonly("control") and self.keycode in self.parent.cursorkeys and self.parent.valid_window() ):
            self.action = "sizewin_br"
            
        else:
            self.action = False
        
        return self.action


    
