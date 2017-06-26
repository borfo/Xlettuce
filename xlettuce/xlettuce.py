#!/usr/bin/python3
# simple tiling grid manager - customizable grid.
# disable capslock in keyboard settings.  Capslock key activates xlettuce

import logging, Xlib, Xlib.display, os, subprocess, time, re
import xutils, xl_config, psutil

# set up logging

# logging.debug(dir(e)) # will list all evdev keyboard key names

class Xlettuce:
    """a simple window tiler.  Runs in the background under X. windows can be moved/resized to sectors of the screen (defaults to a 10x4 grid)
    by pressing two hotkeys - the first corresponds to the new top left location of the active window, and the second corresponds to the new
    lower right corner of the window.  (capslock must be disabled in Keyboard settings.  Enable two shift buttons enables caps lock, one shift disables.)
    Press CAPSLOCK + 12345,qwert,asdfg,zxcv or b for top left coordinate, then hold CAPSLOCK and press another key for bottom right coordinate.
    Once you've pressed two keys, the window moves to that grid position"""
    
    # define cursor keys
    cursorkeys =  [111, 113, 114, 116]
    
    # initialize hotkey map - maps event codes to keyboard grid locations
    tilekeymap = { 10:(0, 0),  11: (1, 0),  12: (2, 0),  13: (3, 0),  14: (4, 0),  15: (5, 0), 16: (6, 0), 17: (7, 0), 18: (8, 0), 19: (9, 0),
    24:(0, 1),  25:(1, 1),  26:(2, 1),  27:(3, 1),  28:(4, 1),  29:(5, 1), 30: (6, 1), 31: (7, 1), 32: (8, 1), 33: (9, 1),
    38:(0, 2),  39:(1, 2),  40:(2, 2),  41:(3, 2),  42:(4, 2),  43:(5, 2), 44: (6, 2), 45: (7, 2), 46: (8, 2), 47: (9, 2),
    52:(0, 3),  53:(1, 3),  54:(2, 3),  55:(3, 3),  56:(4, 3),  57:(5, 3), 58: (6, 3), 59: (7, 3), 60: (8, 3), 61: (9, 3) }

    # initialize hotkey map - maps numpad event codes to 3x3 grid of workspaces/virtual desktops (maps keycode to zero based workspace #)
    desktopkeymap = { 79:0,  80:1,  81:2,
                     83:3, 84:4, 85:5,
                     87:6, 88:7, 89:8}

    # dict with keycode as key, value is a tuple made up of the modmap, the command, then followed by arbitrary number of args
    # this is used to enable hotkey shortcuts when xlettuce detects
    hotkeys = {67: (0, "~/Scripts/setWacom.sh", "map1", "PAD9x12"),
               68: (0, "~/Scripts/setWacom.sh", "map2", "PAD9x12"),
               69: (0, "~/Scripts/setWacom.sh", "map3", "PAD9x12") }
    
    
    def __init__(self):
        """Initializes the tiling grid.  Sets the screen area, grid size, etc.  Defaults to primary monitor at 0,0."""
        
        self.sleeptime=0.05
        
        self.trigger_keycode = 66 # caps lock
        
        # load config
        self.conf = xl_config.xl_config(self)
        
        # start logger
        logging.getLogger( __name__ )
        logging.basicConfig(filename=self.conf.get("GENERAL", "Log_File"), level=self.conf.get("GENERAL", "Log_Level"),  format='%(asctime)s %(message)s')
        logging.getLogger().addHandler(logging.StreamHandler()) # also output log msgs to stdout
        logging.info('Xlettuce launched')




        # initialize tracking vars
        self.isActive = False # initialize var that tracks capslock button state - held down = isActive
        self.firstX = -1 # initialize var that tracks tiling destination
        self.firstY = -1 # initialize var that tracks tiling destination
        self.shift = False # state of shift key modifier
        self.ctrl = False # state of left ctrl key
        self.alt = False # state of left alt key
        self.modnone = True # if no mods are pressed, this is true
        self.currentMonitor = 0 # which monitor are we working on
        
        #probe X for info about screen layout, return screen object
        self.screen = xutils.Screen(self)

        #alias xlib objects
        self.display = self.screen.display
        self.root = self.screen.root
        
        #set key grabs for all possible modifier combinations of the Xlettuce trigger key - 66 is CAPS_LOCK
        self.screen.set_grab_trigger(66)

        #set number of desktops - 9 (3x3) is default - best for numberpad navigation
        self.screen.set_num_desktops(9)
        
        # main loop
        while True:
            self.e = xutils.KeyEvent(self.display.next_event(), self)

            if ( self.e.is_mapping_notify ):
                # mapping has changed.  update the keymap cache, then skip to next event.
                self.display.refresh_keyboard_mapping(self.e.event)
                time.sleep(self.sleeptime)
                continue


            try:
                self.activeWindow = self.screen.get_active_window()
                self.currentMonitor = self.screen.get_current_monitor( self.e.event )
                
                # process event
                self.e.get_mods()
                self.e.get_action()
                
                logging.debug(self.e.action)

                if ( self.e.action == False ): 
                    # key event didn't match any hotkey - skip to next event
                    time.sleep(self.sleeptime)
                    continue
            
                elif ( self.e.action == "trigger_press" ): 
                    self.screen.grab_keyboard()
                    self.isActive=True; 
                    self.firstX = self.firstY = -1 # reset moveto X Y values

                elif ( self.e.action == "trigger_release" ):
                    self.screen.ungrab_keyboard()
                    self.isActive=False
                    self.firstX = self.firstY = -1 # reset moveto X Y values

                elif ( not self.isActive ):
                    time.sleep(self.sleeptime)
                    continue

                elif ( self.e.action == "set_monitor_0" ):
                    self.currentMonitor = 0

                elif ( self.e.action == "set_monitor_1" ):
                    self.currentMonitor = 1

                elif ( self.e.action == "set_monitor_2" ):
                    self.currentMonitor = 2

                elif ( self.e.action == "set_monitor_3" ):
                    self.currentMonitor = 3

                elif ( self.e.action == "tilekey" ):
                    # one of the tiling position hotkeys was pressed
                    self.tilekey( self.e.keycode )

                elif ( self.e.action == "desktopkey" ):
                    # one of the virtual desktop hotkeys was pressed
                    self.desktopkey( self.e.keycode )

                elif ( self.e.action == "movewin" ):
                    # HOTKEY+Cursor, no mods = move window on grid
                    self.movewin(self.e.keycode)

                elif ( self.e.action == "sizewin_tl" ):
                    # Shift+HOTKEY+cursor=resize top left
                    self.sizewinTL(self.e.keycode)

                elif ( self.e.action == "sizewin_br" ):
                    # Ctrl+HOTKEY+cursor=resize bottom right
                    self.sizewinBR(self.e.keycode)
                    

            except AttributeError as err:
                logging.debug("AttributeError: State - caught = " + str(err) )
                #logging.debug("activewininfo = " + str(self.activeWindow.info) )

            except Xlib.error.BadDrawable as err:
                logging.debug("error.BadDrawable: State - caught = " + str(err) )
                #logging.debug("activewininfo = " + str(self.activeWindow.info) )

            time.sleep(self.sleeptime)


    def valid_window( self ):
        '''check if the current active window is a valid moveable window, and not the root window, desktop, etc.
        '''
        if ( self.activeWindow != self.root and ( str(self.activeWindow.info['WM_NAME']).lower() !=  "desktop" ) ):
            return True
        else:
            return False

    
    def is_onscreen(self, x, y):
        '''check if a given coordinate is within the bounds of the monitor's workarea'''
        if ( x >= self.screen.monitor[self.currentMonitor].workarea.screenX and
            x <= self.screen.monitor[self.currentMonitor].workarea.screenX + self.screen.monitor[self.currentMonitor]['width'] and
            y >= self.screen.monitor[self.currentMonitor].workarea.screenY and
            y <= self.screen.monitor[self.currentMonitor].workarea.screenY + self.screen.monitor[self.currentMonitor]['height'] ):
            
            return True
        else:
            return False
    
    def is_ongrid(self, x, y):
        '''check if a pair of coordinates are on the valid tilekey grid for the current monitor'''
        if ( x<0 or y<0 or
            x > (self.screen.monitor[self.currentMonitor].lattice.gridX - 1) or
            y > (self.screen.monitor[self.currentMonitor].lattice.gridY - 1) ):
            return False
        else:
            return True
        
    def get_grid_screenX(self, x):
        '''gets the screen X coordinate for a given tilekey grid coordinate'''
        screenX = self.screen.monitor[self.currentMonitor].workarea.screenX + ( self.screen.monitor[self.currentMonitor].lattice.slotWidth * x )
        return screenX
        
    def get_grid_screenY(self, y):
        '''gets the screen X coordinate for a given tilekey grid coordinate'''
        screenY = self.screen.monitor[self.currentMonitor].workarea.screenY + ( self.screen.monitor[self.currentMonitor].lattice.slotHeight * y )
        return screenY
                
    def get_gridmoveY(self, dir):
        '''calculate new y position after a gridmove.
        dir = "up" or "down"'''
        px_offset={"up":-30, "down":30}
        grid_offset={"up":0, "down":1}
        newY = self.screen.monitor[self.currentMonitor].workarea.screenY + ( ( self.activeWindow.info['containergeom'].y - self.screen.monitor[self.currentMonitor].workarea.screenY + px_offset[dir] ) // self.screen.monitor[self.currentMonitor].lattice.slotHeight + grid_offset[dir] ) * self.screen.monitor[self.currentMonitor].lattice.slotHeight
        if newY < self.screen.panel_top :
            newY = self.screen.panel_top
        if newY > self.screen.avail_height + self.screen.panel_top:
            newY = self.screen.avail_height + self.screen.panel_top - self.activeWindow.info['fullheight']
        
        return newY
        
    def get_gridmoveX(self, dir):
        '''calculate new x position after a gridmove.
        dir = "left" or "right"'''
        px_offset={"left":-30, "right":30}
        grid_offset={"left":0, "right":1}
        newX = self.screen.monitor[self.currentMonitor].workarea.screenX + ( ( self.activeWindow.info['containergeom'].x - self.screen.monitor[self.currentMonitor].workarea.screenX + px_offset[dir] ) // self.screen.monitor[self.currentMonitor].lattice.slotWidth + grid_offset[dir] ) * self.screen.monitor[self.currentMonitor].lattice.slotWidth
        if newX < self.screen.panel_top :
            newX = self.screen.monitor[self.currentMonitor].workarea.screenX
        if newX > self.screen.monitor[self.currentMonitor].workarea.width + self.screen.monitor[self.currentMonitor].workarea.screenX :
            newX = self.screen.monitor[self.currentMonitor].workarea.width + self.screen.monitor[self.currentMonitor].workarea.screenX - self.screen.monitor[self.currentMonitor].lattice.slotWidth
        
        return newX

    def get_gridresize_height(self, dir, corner="BR"):
        '''calculate new height after a gridmove.'''
        if (corner=="TL"):
            px_offset={"up":30, "down":-30}
            grid_offset={"up":1, "down":0}
        else:
            px_offset={"up":-30, "down":30}
            grid_offset={"up":0, "down":1}

        height = ( ( self.activeWindow.info['containergeom'].height + px_offset[dir] ) // self.screen.monitor[self.currentMonitor].lattice.slotHeight + grid_offset[dir] ) * self.screen.monitor[self.currentMonitor].lattice.slotHeight
        if height < self.screen.monitor[self.currentMonitor].lattice.slotHeight :
            height = self.screen.monitor[self.currentMonitor].lattice.slotHeight
        if height > self.screen.monitor[self.currentMonitor].height :
            height = self.screen.monitor[self.currentMonitor].height
        if height+self.activeWindow.info['containergeom'].y > self.screen.monitor[self.currentMonitor].workarea.height + self.screen.monitor[self.currentMonitor].workarea.screenY:
            height = self.screen.monitor[self.currentMonitor].height - self.activeWindow.info['containergeom'].y
        
        return height
        
    def get_gridresize_width(self, dir, corner="BR"):
        '''calculate new width after a gridmove.'''
        if (corner=="TL"):
            px_offset={"left":30, "right":-30}
            grid_offset={"left":1, "right":0}
        else:
            px_offset={"left":-30, "right":30}
            grid_offset={"left":0, "right":1}
            
        width = ( ( self.activeWindow.info['containergeom'].width + px_offset[dir] ) // self.screen.monitor[self.currentMonitor].lattice.slotWidth + grid_offset[dir] ) * self.screen.monitor[self.currentMonitor].lattice.slotWidth
        if width < self.screen.monitor[self.currentMonitor].lattice.slotWidth :
            width = self.screen.monitor[self.currentMonitor].lattice.slotWidth
        if width > self.screen.monitor[self.currentMonitor].width :
            width = self.screen.monitor[self.currentMonitor].width
        if width+self.activeWindow.info['containergeom'].x > self.screen.monitor[self.currentMonitor].workarea.width + self.screen.monitor[self.currentMonitor].workarea.screenX:
            width = self.screen.monitor[self.currentMonitor].width - self.activeWindow.info['containergeom'].x
        
        return width
        
        
    def movewin(self,  keycode):
        '''move active window according to grid using cursor keys.'''

        newx = -1
        newy = -1

        if ( keycode == 111 ): #cursor up
            newy = self.get_gridmoveY('up')
        if ( keycode == 116 ): #cursor down
            newy = self.get_gridmoveY('down')
        if ( keycode == 113 ): #cursor left
            newx = self.get_gridmoveX('left')
        if ( keycode == 114 ): #cursor right
            newx = self.get_gridmoveX('right')
            
        self.configureWin(newx, newy, -1, -1)


    def sizewinBR(self,  keycode):
        '''resize active window according to grid using cursor keys. - change bottom and right edge'''

        width = -1
        height = -1

        if ( keycode == 111 ): #cursor up
            height = self.get_gridresize_height('up')
        if ( keycode == 116 ): #cursor down
            height = self.get_gridresize_height('down')
        if ( keycode == 113 ): #cursor left
            width = self.get_gridresize_width('left')
        if ( keycode == 114 ): #cursor right
            width = self.get_gridresize_width('right')

        self.configureWin(-1, -1, width, height)


    def sizewinTL(self,  keycode):
        '''resize active window according to grid using cursor keys. - change top and left edge'''
        newx = -1
        newy = -1
        width = -1
        height = -1

        if ( keycode == 111 and ( self.activeWindow.info['containergeom'].y - 10 ) > self.screen.monitor[self.currentMonitor].workarea.screenY ): #cursor up
            newy = self.get_gridmoveY('up')
            height = self.get_gridresize_height('up', 'TL')

        if ( keycode == 116 and ( self.activeWindow.info['containergeom'].height + 10 ) // self.screen.monitor[self.currentMonitor].lattice.slotHeight > 1): #cursor down
            newy = self.get_gridmoveY('down')
            height = self.get_gridresize_height('down', 'TL')

        if ( keycode == 113 and ( self.activeWindow.info['containergeom'].x - 10 ) > self.screen.monitor[self.currentMonitor].workarea.screenX ): #cursor left
            newx = self.get_gridmoveX('left')
            width = self.get_gridresize_width('left', 'TL')

        if ( keycode == 114 and ( self.activeWindow.info['containergeom'].width + 10 ) // self.screen.monitor[self.currentMonitor].lattice.slotWidth > 1 ): #cursor right
            newx = self.get_gridmoveX('right')
            width = self.get_gridresize_width('right', 'TL')

        self.configureWin(newx, newy, width, height)


    def tilekey(self,  keycode):
        '''Tiling position hotkeys - based on grid.  HOLD capslock +key sets upper left corner, keep holding capslock then +key sets lower right corner.'''
        window = self.activeWindow

        if ( self.e.modshift ):
            # while shift is held down x coordinate is doubled - grid slots are twice as wide, grid is composed of half as many keys.
            X = self.tilekeymap[keycode][0] * 2 
        else:
            X = self.tilekeymap[keycode][0]

        Y = self.tilekeymap[keycode][1]

        if ( not self.is_ongrid(X, Y) ) : # make sure tilekey grid coordinates are within valid range
            return False
        
        if self.firstX == -1 or self.firstY == -1 :
            # this is the first tiling button press, set top left coordinates
            self.firstX = X
            self.firstY = Y
        else:
            secondX = X
            secondY = Y
            width = secondX - self.firstX
            height = secondY - self.firstY
            
            if ( width < 0 or height < 0 ):
                #switch first and second
                tempx = self.firstX
                tempy = self.firstY
                self.firstX = secondX
                self.firstY = secondY
                secondX = tempx
                secondY = tempy
            
            # translate grid coordinates into screen coordinates
            self.firstX = self.get_grid_screenX( self.firstX )
            self.firstY = self.get_grid_screenY( self.firstY )
            secondX = self.get_grid_screenX( secondX + 1 ) - 1
            secondY = self.get_grid_screenY( secondY + 1 ) - 1
            width = secondX - self.firstX
            height = secondY - self.firstY


            # make sure move location is within range
            if self.is_onscreen(self.firstX, self.firstY) and self.is_onscreen(secondX, secondY) and ( width > 0 ) and ( height > 0 ) :
                self.configureWin( self.firstX, self.firstY, width, height )

            # reset moveto X Y values
            self.firstX = -1
            self.firstY = -1

    def configureWin( self, x, y, width, height ):
        '''Move and resize window.'''

        #set position and dimensions = -1 means don't change
        if x == -1 :
            x = self.activeWindow.info['containergeom'].x
        if y == -1 :
            y = self.activeWindow.info['containergeom'].y
        if width == -1 :
            width = self.activeWindow.info['containergeom'].width
        if height == -1 :
            height = self.activeWindow.info['containergeom'].height

        targetX=x
        targetY=y
        targetWidth=width
        targetHeight=height

        #correct for window container padding
        x = ( x + self.activeWindow.info['padleft'] )
        y = ( y + self.activeWindow.info['padtop'] )
        width = ( width - self.activeWindow.info['padleft'] - self.activeWindow.info['padright'] )
        height = ( height - self.activeWindow.info['padtop'] - self.activeWindow.info['padbottom'] )


        #reposition window
        logging.debug("POSITION window.configure(x=%d,  y=%d,  width=%d,  height=%d)" % (x, y, width, height))
        self.activeWindow.configure(x=x,  y=y,  width=width,  height=height)

        self.activeWindow.info=self.screen.get_xwininfo(self.activeWindow)

        #test position - some windows (GTK I think) reposition themselves when reparented toadd title bar, so they're off on Y axis by the titlebar height
        contX=self.activeWindow.info['containergeom'].x
        contY=self.activeWindow.info['containergeom'].y
        contWidth=self.activeWindow.info['containergeom'].width
        contHeight=self.activeWindow.info['containergeom'].height

        logging.debug("x %s - y %s - width %s - height %s" % (x,  y,  width,  height ))
        logging.debug("contx %s - conty %s - contwidth %s - contheight %s" % (contX,  contY,  contWidth,  contHeight ))
        logging.debug("targetx %s - targety %s - targetwidth %s - targetheight %s" % (targetX, targetY,  targetWidth, targetHeight ))

        #for k in self.activeWindow.info['WM_NORMAL_HINTS']:
            #print("wnh: %s -- %s" % (bin(k), k))

        change = False
        if ( contX != targetX ):
            x = x + ( targetX - contX )
            change = True
        if ( contY != targetY ):
            y = y + ( targetY - contY )
            change = True
        if ( contHeight != targetHeight ):
            height = height + ( targetHeight - contHeight )
            change = True
        if ( contWidth != targetWidth ):
            width = width + ( targetWidth - contWidth )
            change = True

        if (x<0 or y<0 or width<0 or height<0):
            # one of the values is negative - one way this happens is when we try to resize a window smaller than its minimum size
            return False

        if change == True:
            #reposition window
            logging.debug("TEST REPOSITION window.configure(x=%d,  y=%d,  width=%d,  height=%d)" % (x, y, width, height))
            self.activeWindow.configure(x=x,  y=y,  width=width,  height=height)

        self.display.flush()


    def desktopkey(self,  keycode):
        '''Desktop hotkeys - 3x3 grid.  HOLD capslock + numpad key moves to different desktop.'''

        window = self.activeWindow

        if ( self.e.modonly("alt") ) and ( self.valid_window() ):
            # send window to different desktop, then change view to that desktop as well
            logging.debug("desktop - alt - sendwin, follow")
            self.screen.send_event( window, self.display.intern_atom("_NET_WM_DESKTOP"), [self.desktopkeymap[keycode]] )
            self.screen.send_event( self.root, self.display.intern_atom("_NET_CURRENT_DESKTOP"), [self.desktopkeymap[keycode]] )

        elif ( self.e.modonly("control") ) and ( window != self.root ) and ( self.activeWindow.info['WM_NAME'].lower() !=  "desktop" ):
            logging.debug("desktop - ctrl - sendwin, don'tfollow")
            # send window to different desktop, keep view on current desktop
            self.screen.send_event( window, self.display.intern_atom("_NET_WM_DESKTOP"), [self.desktopkeymap[keycode]] )

        elif ( self.modnone ):
            logging.debug("desktop - modnone - don't sendwin, go to desktop")
            # switch to desktop ##
            self.screen.send_event( self.root, self.display.intern_atom("_NET_CURRENT_DESKTOP"), [self.desktopkeymap[keycode]] )




if __name__ == "__main__":
    # running as tiling script
    
    # Check if script is already running, if so, kill it.
    pidfilename="/xlettuce.pid"
    pidfilename=str(os.path.dirname(os.path.realpath(__file__)))+pidfilename
    print("FILENAME: %s" % pidfilename)
    if (os.path.isfile(pidfilename)):
        with open(pidfilename) as f:
            oldpid = int(f.read())
        print("OLD: %i" % oldpid)
        
        if ( psutil.pid_exists(oldpid) ):
            p=psutil.Process(oldpid)
            if ( "xlettuce" in p.name().lower() ):
                print ( "Xlettuce is already running: %s " % p.name() )
                exit()
    
    # write PID to file
    pid=str(os.getpid())
    pidfile = open(pidfilename, 'w')
    pidfile.write(pid)
    pidfile.close()
    
    # run tiler
    xlettuce = Xlettuce()
    
    os.remove(pidfilename)

