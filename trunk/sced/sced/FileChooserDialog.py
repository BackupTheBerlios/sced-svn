#-*- coding: utf-8 -*-

import gtk
import sced

class FileChooserDialog(gtk.FileChooserDialog):

    __gsignals__ = {
        "response": "override",
    }
    
    def __init__(self, title=None,
            parent=None,
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=None,
            backend=None):
        gtk.FileChooserDialog.__init__(self, title,
            parent,
            action,
            buttons,
            backend)
        
        self.__f1 = gtk.FileFilter()
        self.__f1.set_name(_("SuperCollider files") + " (*.sc; *.scd)")
        self.__f1.add_pattern("*.sc")
        self.__f1.add_pattern("*.scd")
        self.add_filter(self.__f1)
        
        #self.__f2 = gtk.FileFilter()
        #self.__f2.set_name(_("Python files") + " (*.py)")
        #self.__f2.add_pattern("*.py")
        #self.add_filter(self.__f2)
        
        self.__f0 = gtk.FileFilter()
        self.__f0.set_name(_("All Files"))
        self.__f0.add_pattern("*")
        self.add_filter(self.__f0)
        
        # filter preserved between dialogs (and sessions)
        default = sced.prefs.get("General", "default-file-type")
        if default == 1:
            self.set_filter(self.__f1)
        #elif default == 2:
        #    self.set_filter(self.__f2)
        else:
            self.set_filter(self.__f0)
    
    # filter preserved between dialogs (and sessions)
    def do_response(self, response_id):
        if response_id == gtk.RESPONSE_OK:
            if self.get_filter() is self.__f1:
                sced.prefs.set("General", "default-file-type", 1)
            #elif self.get_filter() is self.__f2:
            #    sced.prefs.set("General", "default-file-type", 2)
            else:
                sced.prefs.set("General", "default-file-type", 0)
