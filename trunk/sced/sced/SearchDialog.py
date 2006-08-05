#-*- coding: utf-8 -*-

import gtk

class SearchDialog (gtk.Dialog):
    def __init__ (self, parent = None, title = _("Find")):
        gtk.Dialog.__init__ (self,
                title = title,
                parent = parent,
                flags = 0,
                buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE))

        self.__entry1 = gtk.Entry ()
        self.vbox.pack_start (self.__entry1)
        self.__entry1.show ()

class ReplaceDialog (SearchDialog):
    def __init__ (self, parent):
        SearchDialog.__init__ (self, parent = parent, title = _("Replace"))

    def replace (self):
        pass
