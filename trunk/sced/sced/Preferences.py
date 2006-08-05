# -*- coding: utf-8 -*-

import os
import ConfigParser

import gobject # for signalling!
import sced

defaults = {
    "General/runtime-dir":          ("",                "get"),
    "General/default-file-type":    (1,                 "getint"),
    
    "General/toolbar-visible":      (1,                 "getboolean"),
    "General/statusbar-visible":    (1,                 "getboolean"),
    "General/output-visible":       (1,                 "getboolean"),
    
    "Geometry/width":               (600,               "getint"),
    "Geometry/height":              (800,               "getint"),
    
    "Editing/use-default-font":     (1,                 "getboolean"),
    "Editing/font":                 ("Monospace 12",    "get"),
    "Editing/log-font":             ("Monospace 12",    "get"),
    "Editing/auto-indent":          (1,                 "getboolean"),
    
    "Recording/format":             (sced.REC_FORMAT_AIFF,   "getint"),
    "Recording/sample":             (sced.REC_SAMPLE_FLOAT,  "getint"),
    "Recording/channels":           (2,                 "getint"),
    "Recording/use-default-dir":    (1,                 "getboolean"),
    "Recording/dir":                ("",                "get"),
}

class Preferences(gobject.GObject):
    __gsignals__ = {
        "changed": (gobject.SIGNAL_RUN_LAST,
            gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING)),
    }
    
    def __init__(self):
        gobject.GObject.__init__(self)
        
        self.__parser = ConfigParser.SafeConfigParser()        
        self.__path = os.path.join(os.environ["HOME"],
                                   ".config", "Sced", "Preferences")
        
        if not os.path.exists(self.__path):
            if not os.path.isdir(os.path.dirname(self.__path)):
                os.makedirs(os.path.dirname(self.__path))
            open(self.__path, "w").close()
        
        self.__parser.read(self.__path)
        
        if not self.__parser.has_section("General"):
            self.__parser.add_section("General")
        
        if not self.__parser.has_section("Geometry"):
            self.__parser.add_section("Geometry")
        
        if not self.__parser.has_section("Editing"):
            self.__parser.add_section("Editing")
        
        if not self.__parser.has_section("Recording"):
            self.__parser.add_section("Recording")
    
    def get(self, section, name):
        default, get_method = defaults["/".join([section, name])]
        get_method = getattr(self.__parser, get_method)
        try:
            value = get_method(section, name)
        except ConfigParser.NoOptionError:
            value = default
            self.set(section, name, value)
        return value
    
    # this is also going to notify interested things
    def set(self, section, name, value):
        self.__parser.set(section, name, unicode(value))
        self.__parser.write(open(self.__path, "w"))
        self.emit("changed", section, name)
