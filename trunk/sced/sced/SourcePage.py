#-*- coding: utf-8 -*-

# FIXME: should I subclass gtksourceview instead?

import gobject
import pango
import gtk
import gtksourceview

import sced

class SourcePage(gtk.ScrolledWindow):

    __gsignals__ = {
            "update-ui":
                    (gobject.SIGNAL_RUN_LAST,
                     gobject.TYPE_NONE,
                     ()),
            "update-cursor":
                    (gobject.SIGNAL_RUN_LAST,
                     gobject.TYPE_NONE,
                     (gobject.TYPE_INT, gobject.TYPE_INT)),
    } # __gsignals__

    def __init__ (self, buffer):
        gtk.ScrolledWindow.__init__ (self)

        self.props.shadow_type = gtk.SHADOW_IN
        self.props.hscrollbar_policy = gtk.POLICY_AUTOMATIC
        self.props.vscrollbar_policy = gtk.POLICY_AUTOMATIC
        
        self.buffer = buffer

        self.view = gtksourceview.SourceView (self.buffer)
        
        if sced.prefs.get("Editing", "use-default-font"):
            font = None
        else:
            font = sced.prefs.get("Editing", "font")
        self.view.modify_font (pango.FontDescription (font))
        sced.prefs.connect("changed", self.__notify_font)
        self.view.props.auto_indent = True

        self.add (self.view)
        self.view.show ()

        self.view.connect_after("toggle-overwrite", self.__on_ui_signal)
        self.view.connect("button-press-event", self.__on_view_button_press)
        self.buffer.connect("changed", self.__on_ui_signal)
        self.buffer.connect("modified-changed", self.__on_ui_signal)
        
        self.buffer.connect("mark-set", self.__on_cursor_signal)

    def __on_ui_signal (self, *args):
        #print "UI>>", args
        self.emit ("update-ui")

    def __on_cursor_signal (self, buffer, iter, mark):
        line = iter.get_line()
        char = iter.get_line_offset()
        self.emit ("update-cursor", line, char)

    def __on_view_button_press (self, view, event):
        if event.type == gtk.gdk._2BUTTON_PRESS:
            x, y = self.view.window_to_buffer_coords(gtk.TEXT_WINDOW_WIDGET,
                int(event.x),
                int(event.y))

            iter1 = self.view.get_iter_at_location(x,y)
            iter1.set_line_offset(0)

            iter2 = iter1.copy()
            iter2.forward_to_line_end()

            if sced.is_block_beginning(self.buffer.get_text(iter1, iter2)):
                try:
                    start, end = self.buffer.find_block(iter1)
                    self.buffer.select_range(start, end)
                finally:
                    # although block not available, return True anyway
                    return True
        return False

    def __notify_font(self, prefs, section, name):
        pref = "/".join([section, name])
        if pref == "Editing/font" or pref == "Editing/use-default-font":
            if sced.prefs.get("Editing", "use-default-font"):
                font = None
            else:
                font = sced.prefs.get("Editing", "font")
            self.view.modify_font (pango.FontDescription (font))
