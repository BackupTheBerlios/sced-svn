# -*- coding: utf-8 -*-

import gobject
import gtk

class QuitConfirmationDialog (gtk.MessageDialog):
    def __init__(self, parent=None, unsaved=[]):
        gtk.MessageDialog.__init__(self,
            parent=parent,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_WARNING,
            buttons=gtk.BUTTONS_NONE,
            message_format=_("%d files have unsaved changes") % 1)
        
        self.format_secondary_markup("Choose the files you want to save:")
        #self.props.default_height = 640
        
        self.add_button (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        self.add_button (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        self.add_button (gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        self.set_default_response (gtk.RESPONSE_OK)
        
        frame = gobject.new(gtk.Frame, shadow_type = gtk.SHADOW_IN)
        self.label.parent.add(frame)
        frame.show()
        
        tv = gobject.new (gtk.TreeView,
            model=self.__create_model(unsaved),
            headers_visible=False)
        frame.add(tv)
        tv.show()
        
        col = gtk.TreeViewColumn ("", gtk.CellRendererToggle(), active=0)
        tv.append_column(col)
        
        cell = gtk.CellRendererText()
        col = gtk.TreeViewColumn ("", cell)
        col.set_cell_data_func (cell, self.__cell_data_func)
        tv.append_column(col)
    
    def __create_model (self, unsaved):
        # is pyobject right?
        model = gtk.ListStore(gobject.TYPE_BOOLEAN, gobject.TYPE_PYOBJECT)
        
        for page in unsaved:
            iter = model.append ()
            model.set (iter, 0, True)
            model.set (iter, 1, page.buffer)
        
        return model
    
    def __cell_data_func(self, column, cell, model, iter):
        buffer = model.get_value(iter, 1)
        filename = buffer.get_title()
        if filename is None:
            filename = "Jobba"
        cell.props.text = filename
