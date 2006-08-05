#-*- coding: utf-8 -*-

import gobject
import gtk

class SourcePageLabel(gtk.HBox):
    __gsignals__ = {
            "close-button-clicked":
                (gobject.SIGNAL_RUN_LAST,
                 gobject.TYPE_NONE, ()),
    } # __gsignals__

    def __init__(self, page):
        gtk.HBox.__init__(self, spacing=6)

        img = gtk.image_new_from_stock(gtk.STOCK_FILE, gtk.ICON_SIZE_MENU)
        self.pack_start(img, expand=False, fill=False)
        img.show()

        self.__label = gtk.Label(page.buffer.get_title())
        self.pack_start(self.__label)
        self.__label.show()

        button = gtk.Button()
        self.pack_start(button)
        button.set_relief(gtk.RELIEF_NONE)
        button.props.focus_on_click = False
        image = gtk.image_new_from_stock(gtk.STOCK_CLOSE, gtk.ICON_SIZE_MENU)
        button.set_size_request(18, 18)

        button.add(image)
        button.show_all()
        button.connect("clicked", self.__on_close_button_clicked)
        
        page.buffer.connect("title-updated", self.__on_buffer_title_updated)
        page.buffer.connect("modified-changed", self.__on_buffer_title_updated)
    
    def set_text(self, text):
        self.__label.set_text(text)

    def __on_close_button_clicked(self, button):
        self.emit("close-button-clicked")
    
    def __on_buffer_title_updated(self, buffer):
        text = buffer.get_title()
        if buffer.get_modified():
            text = "*" + text
        self.__label.set_text(text)
