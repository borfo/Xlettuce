#!/usr/bin/python3

# config file loading, parsing, saving functions

import configparser, weakref
from collections import OrderedDict

class xl_config:
    configfile = "./xlettuce.conf"
    
    parsefunctions = {
            "STR":str,
            "INT":int,
            "BOOL":bool,
            "FLOAT":float
    }
    
    parser = configparser.ConfigParser( dict_type=OrderedDict, allow_no_value=True , inline_comment_prefixes=("#",) )
    
    def __init__(self, parent):
        self.parent = weakref.proxy(parent)
        self.settings_read=False # set to true once a settings file has been read into self.key
        self.read_key()
        self.load_file()
        self.read_values()
            
    def read_key(self):
        # store key to the config file
        # OrderedDict containing
        # ['SECTION']['SETTING_NAME'] = list [ type, default_value, force_default, comment, value=Null ]
        ##### [0] STR type --> int/float/bool/str default=str - this is used to autoconvert the value to the right type on load.  If it's empty, value is loaded as a string.
        ##### [1] STR default_value --> this is fed to configparser to build a new configfile
        ##### [2] BOOL force_default --> if True, then the default value will be loaded if this setting is left blank
        ##### [3] STR comment --> inline comment to be printed at the end of the line
        ##### [4] BOOL/FLOAT/INT/STR value --> value loaded from config file (Null until conf file is parsed) 
           
        ########################### GENERAL SETTINGS
        key = OrderedDict()
        key['GENERAL'] = OrderedDict()
        key['GENERAL']['XLettuce_Key'] =  [ 'INT', 66, True, "Keycode of the key you want dedicated to activating Xlettuce.  [eg: capslock=66, scroll lock=78, pause/break=127]", "" ]
        key['GENERAL']['Alternate_Key'] =  [ 'INT', 0, True, "Optional - if you want a second activation key, enter the keycode here.]", "" ]
        key['GENERAL']['Log_Level'] =  [ 'STR', "DEBUG", True, "DEBUG, INFO, WARNING, ERROR, CRITICAL", "" ]
        key['GENERAL']['Log_File'] =  [ 'STR', "./xlettuce.log", True, "Path to log file", "" ]
        key['GENERAL']['Log_Overwrite'] =  [ 'BOOL', True, True, "Overwrite log file every session?  True/False", "" ]
        
        ########################### LAUNCHERS
        key['LAUNCHERS'] = OrderedDict()
        key['LAUNCHERS']['comment'] = "# Hold XLettuce activation key + these launcher keys to launch custom commands/scripts/apps."
        key['LAUNCHERS']['comment2'] = "# enter the command to run with each launcher in the settings below."
    
        key['LAUNCHERS']['f1'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f2'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f3'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f4'] = [ 'STR', "", True, "", "" ]
    
        key['LAUNCHERS']['f5'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f6'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f7'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f8'] = [ 'STR', "", True, "", "" ]
    
        key['LAUNCHERS']['f9'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f10'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f11'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['f12'] = [ 'STR', "", True, "", "" ]
        
        key['LAUNCHERS']['SHIFT+f1'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f2'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f3'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f4'] = [ 'STR', "", True, "", "" ]
    
        key['LAUNCHERS']['SHIFT+f5'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f6'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f7'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f8'] = [ 'STR', "", True, "", "" ]
    
        key['LAUNCHERS']['SHIFT+f9'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f10'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f11'] = [ 'STR', "", True, "", "" ]
        key['LAUNCHERS']['SHIFT+f12'] = [ 'STR', "", True, "", "" ]
        
        ########################### HEADS UP DISPLAY APPS
        key['HUD'] = OrderedDict()
        key['HUD']['comment'] = "# Heads Up Display - specify up to 4 commonly used apps to run in special 'HUD' slots."
        key['HUD']['comment2'] = "# XLettuce_Key+HUD_Hotkey makes the app appear and disappear above your other windows, in the same location every time."
        key['HUD']['comment3'] = "# Ideal for utility apps you use all the time - terminals, txt editor, file manager, etc."
        key['HUD']['comment4'] = "# COMMAND - Command to open your App.  Can accept BASH arguments."
        key['HUD']['comment5'] = "# HOTKEY - Keycode of the key you want to press (+ XLettuce Key) to launch, show, and hide this HUD App."
    
        key['HUD']['App1_Command'] = [ 'STR', "", True, "", "" ]
        key['HUD']['App1_Hotkey'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App1_PosX'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App1_PosY'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App1_Width'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App1_Height'] = [ 'INT', "", True, "", "" ]
    
        key['HUD']['App2_Command'] = [ 'STR', "", True, "", "" ]
        key['HUD']['App2_Hotkey'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App2_PosX'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App2_PosY'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App2_Width'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App2_Height'] = [ 'INT', "", True, "", "" ]
    
        key['HUD']['App3_Command'] = [ 'STR', "", True, "", "" ]
        key['HUD']['App3_Hotkey'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App3_PosX'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App3_PosY'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App3_Width'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App3_Height'] = [ 'INT', "", True, "", "" ]
    
        key['HUD']['App4_Command'] = [ 'STR', "", True, "", "" ]
        key['HUD']['App4_Hotkey'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App4_PosX'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App4_PosY'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App4_Width'] = [ 'INT', "", True, "", "" ]
        key['HUD']['App4_Height'] = [ 'INT', "", True, "", "" ]
        
        ########################### MONITORS
        key['MONITORS'] = OrderedDict()
        key['MONITORS']['comment'] = "# When using multiple monitors, XLettuce defaults to tiling on the currently active monitor."
        key['MONITORS']['comment2'] = "# If you want to tile a window onto a different monitor, press the hotkey specified below while tiling in XLettuce."
        key['MONITORS']['comment3'] = "# XLettuce currently supports a maximum of 4 monitors."
        
        
        key['MONITORS']['Mon0_Hotkey'] =  [ 'INT', 121, True, "", "" ]
        key['MONITORS']['Mon1_Hotkey'] =  [ 'INT', 122, True, "", "" ]
        key['MONITORS']['Mon2_Hotkey'] =  [ 'INT', 123, True, "", "" ]
        key['MONITORS']['Mon3_Hotkey'] =  [ 'INT', 124, True, "", "" ]
        
        key['MONITORS']['Mon0_Grid_X'] =  [ 'INT', 6, True, "", "" ]
        key['MONITORS']['Mon0_Grid_Y'] =  [ 'INT', 4, True, "", "" ]
    
        key['MONITORS']['Mon1_Grid_X'] =  [ 'INT', 6, True, "", "" ]
        key['MONITORS']['Mon1_Grid_Y'] =  [ 'INT', 4, True, "", "" ]
        
        key['MONITORS']['Mon2_Grid_X'] =  [ 'INT', 6, True, "", "" ]
        key['MONITORS']['Mon2_Grid_Y'] =  [ 'INT', 4, True, "", "" ]
        
        key['MONITORS']['Mon3_Grid_X'] =  [ 'INT', 6, True, "", "" ]
        key['MONITORS']['Mon3_Grid_Y'] =  [ 'INT', 4, True, "", "" ]
        
        self.key=key
        return key
    
    def generate_conf_string(self, force_defaults=False):
        '''
        Generate a text file from the 'key' variable.  This can either be used to feed into configparser, or to create a default settings config file.
        set force_defaults to True to generate based on default settings regardless of whether the user has config settings.
        Otherwise, it will generate based on the user's settings if those settings have been read in, or based on defaults if no conf file has been read in.
        Returns a string, or false on failure.
        '''
        
        outstr="#XLettuce configuration file"
        key=self.key
        valref = 4 if (self.settings_read == True and force_defaults == False) else 1
        
        for section in key:
            outstr+="\n["+section+"]\n"
            for name in key[section]:
                item=key[section][name]
                
                if ( name.find("comment", 0, 7) == 0 ) :
                    outstr+=str(item)+"\n"
                else:
                    
                    #get value - either user set value, or default
                    if ( not item[valref] ) and ( item[3] == True):
                        value=str(item[1])
                    else:
                        value=str(item[valref])
                    
                    if (value):
                        outstr+=name+" = "+value
                    else:
                        outstr+=name+" = "
                    
                    #add inline comment
                    outstr += " # "+str(item[3])+"\n" if len(item[3]) > 0 else "\n"

        return(outstr)
    
    
    def load_file(self):
        '''load config file if it exists.  If it doesn't exist, write a new configfile with default values.'''
        try:
            f=open(self.configfile)
        except EnvironmentError:
            self.make_file()
            f=open(self.configfile)
        
        self.parser.read_file( f )
           
            
    def make_file(self):
        '''Writes a new, blank xlettuce config file with default values'''
        confstr=self.generate_conf_string(True)
        print(confstr)
        with open( self.configfile, 'w' ) as configfile:
            configfile.write( confstr )


    def write_file(self):
        '''Writes a new, blank xlettuce config file with default values'''
        self.parser.read_string(self.generate_conf_string(False))
        with open( self.configfile, 'w' ) as configfile:
            self.parser.write( configfile )


    def read_values(self):
        '''read the values from configparser into self.key, parsing for int/bool/float/str types.
        '''
        # check if configparser has any sections - if not, it's not loaded yet.
        if (len(self.parser.sections()) < 1):
            return False
        
        try:
            self.key
        except AttributeError:
            self.read_key()
        
        key = self.key
        for section in key:
            for name in key[section]:
                item=key[section][name]
                if ( name.find("comment", 0, 7) == 0 ) :
                    continue
                
                if ( not self.parser.has_option(section, name) ) :
                    # get default value if force_default is true
                    value = item[1] if (item[2]) else ""
                else:
                    value = self.parser.get(section, name)
                    
                #parse for type, assign
                if (value):
                    item[4] = self.parsefunctions[item[0]](value)
                else:
                    item[4] = ""
                    
        self.settings_read=True
    
    
    def get(self, section, option):
        if ( not self.option_exists(section, option) ):
            print("get false")
            return False

        return self.key[section][option][4]
    
    
    def set(self, section, option, value):
        # check if section and name exist in key
        try:
            self.key
        except AttributeError:
            self.read_key()
        
        if ( not self.option_exists(section, option) ):
            print("set - optexists false")
            return False
        
        try:
            parsedval = self.parsefunctions[self.key[section][option][4]](value)
        except ValueError:
            print("set value error")
            return False
        
        self.key[section][option][4]=parsedval
        self.parser.set(section,option,parsedval)
        return true
      
    def section_exists(self, section):
        if ( section in self.key ):
            return True
        else:
            print("s exists false")
            return False
        
    def option_exists(self, section, option):
        if ( not self.section_exists(section) ):
            print("opt exists false - sec")
            return False
        
        if ( option in self.key[section] ):
            return True
        else:
            print("opt exists opt")
            return False
        
if __name__ == "__main__":
    xlconf = xl_config()

