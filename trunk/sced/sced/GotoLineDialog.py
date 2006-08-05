#-*- coding: utf-8 -*-

import gtk

class GotoLineDialog(gtk.Dialog):
    def __init__(self, parent=None):
        gtk.Dialog.__init__(self, title=_("Go to Line"),
            parent=parent,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_JUMP_TO, gtk.RESPONSE_OK))
        self.set_default_response(gtk.RESPONSE_OK)
        
        # FIXME: connect entry "activate" signal to response
        
        self.entry = gtk.Entry()
        self.vbox.add (self.entry)
        self.entry.show ()
    
    def entry_activate(self):
        pass
