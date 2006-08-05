#-*- coding: utf-8 -*-

import gobject
import gtk

class Statusbar(gtk.Statusbar):
    __gproperties__ = {
        "overwrite-visible": (gobject.TYPE_BOOLEAN,
            "overwrite label visible",
            "if TRUE, the overwrite label is visible",
            True,
            gobject.PARAM_READWRITE),
        "cursor-pos-visible": (gobject.TYPE_BOOLEAN,
            "cursor position label visible",
            "if TRUE, the cursor position label is visible",
            True,
            gobject.PARAM_READWRITE),
    }
    
    def __init__(self):
        gtk.Statusbar.__init__(self)

        self.props.spacing = 0
        self.props.has_resize_grip = False

        self.line_label = gobject.new(gtk.Statusbar, width_request=128)
        self.line_label.props.has_resize_grip = False

        self.pack_start(self.line_label, expand=False, fill=False)
        self.line_label.show()

        self.ins_label = gobject.new(gtk.Statusbar, width_request=64)
        self.ins_label.props.has_resize_grip = True

        self.pack_start (self.ins_label, expand=False, fill=False)
        self.ins_label.show()
        
        self.set_position(0, 0)
    
    def do_get_property(self, property):
        if property.name == "overwrite-visible":
            return self.ins_label.props.visible
        elif property.name == "cursor-pos-visible":
            return self.line_label.props.visible
        else:
            raise AttributeError, "Unknown property %s" % property.name
    
    def do_set_property(self, property, value):
        if property.name == "overwrite-visible":
            self.ins_label.props.visible = value
        elif property.name == "cursor-pos-visible":
            self.line_label.props.visible = value
        else:
            raise AttributeError, "Unknown property %s" % property.name
    
    def set_overwrite(self, overwrite):
        context = self.ins_label.get_context_id("default")
        self.ins_label.pop(context)
        if overwrite:
            self.ins_label.push(context, _("OVR"))
        else:
            self.ins_label.push(context, _("INS"))

    def set_position(self, line, char):
        context = self.line_label.get_context_id("default")
        self.line_label.pop(context)
        self.line_label.push(context, _("Line %d, Col %d") % (line + 1, char + 1))
