# -*- coding: utf-8 -*-

import gobject
import gtk

import sced

# fixme: this also needs to track preference changes from the outside?

# * pong, the prefs dialog RAD tool???
# * need proxies for getting & setting widget values
# * need "custom widget" support in sections, like last arg "custom-widget"
#   in create_section

class PreferencesDialog(gtk.Dialog):

    __gsignals__ = {
        "response":     "override",
        "delete_event": "override",
    }

    def __init__(self, parent):
        gtk.Dialog.__init__(self,
            parent=parent,
            title=_("Sced Preferences"),
            buttons=(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE),
            flags=gtk.DIALOG_NO_SEPARATOR)
        
        self.set_resizable(False)
        
        notebook = gobject.new(gtk.Notebook, border_width=6)
        self.vbox.add(notebook)
        notebook.show()
        
        page = self.__create_general_page()
        notebook.append_page(page, gtk.Label(_("General")))
        page.show()
        
        page = self.__create_editing_page()
        notebook.append_page(page, gtk.Label(_("Editor")))
        page.show()
        
        page = self.__create_page_recording()
        notebook.append_page(page, gtk.Label(_("Recording")))
        page.show()
        
        self.__update_prefs()
    
    def __update_prefs(self):
        self.__gen_dir.set_current_folder(sced.prefs.get("General", "runtime-dir"))
        
        self.__ed_use_default.set_active(sced.prefs.get("Editing", "use-default-font"))
        self.__ed_font.set_font_name(sced.prefs.get("Editing", "font"))
        
        self.__rec_format.set_active(sced.prefs.get("Recording", "format"))
        self.__rec_sample.set_active(sced.prefs.get("Recording", "sample"))
        self.__rec_channels.set_value(sced.prefs.get("Recording", "channels"))
    
    def __create_general_page(self):
        self.__gen_dir = gobject.new(gtk.FileChooserButton,
            title=_("Choose runtime directory"),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        
        sec1 = self.__create_pref_section("Language", [
            (None, gtk.CheckButton("Use internal server by default")),
            ("Runtime directory:", self.__gen_dir),
        ])
        
        return self.__create_pref_page([sec1])
    
    def __create_editing_page(self):
        self.__ed_use_default = gtk.CheckButton("Use default theme font")
        self.__ed_font = gtk.FontButton()
        self.__ed_auto_indent = gtk.CheckButton("Enable auto intendation")
        
        self.__ed_use_default.connect("toggled",
            self.__on_ed_use_default_toggled)
        self.__ed_font.connect("font-set",
            self.__on_ed_font_font_set)
        
        sec1 = self.__create_pref_section("Font", [
            (None,              self.__ed_use_default),
            ("Editor font:",    self.__ed_font),
        ])
        
        sec2 = self.__create_pref_section("Intendation", [
            (None,              self.__ed_auto_indent),
        ])
        
        return self.__create_pref_page([sec1, sec2])
    
    def __create_page_recording(self):
        self.__rec_format = gtk.combo_box_new_text()
        self.__rec_format.append_text("AIFF")
        self.__rec_format.append_text("WAV")
        self.__rec_format.append_text("Au")
        self.__rec_format.append_text("IRCAM")
        self.__rec_format.append_text("Raw")
        
        self.__rec_sample = gtk.combo_box_new_text()
        self.__rec_sample.append_text("8-bit int")
        self.__rec_sample.append_text("16-bit int")
        self.__rec_sample.append_text("32-bit int")
        self.__rec_sample.append_text("Float")
        self.__rec_sample.append_text("Double")
        self.__rec_sample.append_text("μ-law")
        self.__rec_sample.append_text("A-law")
        
        adj = gtk.Adjustment(value=2,
            lower=1,
            upper=255,
            step_incr=1,
            page_incr=2)
        self.__rec_channels = gtk.SpinButton(adj)
        
        rec_default_dir = gtk.CheckButton(_("Use default record path (scdir/recordings)"))
        rec_default_dir.connect("toggled", self.__on_rec_default_dir_toggled)
        
        self.__rec_fc = gobject.new(gtk.FileChooserButton,
            title=_("Choose recording directory"),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        
        sec1 = self.__create_pref_section("Record format", [
            ("File format:", self.__rec_format),
            ("Sample format:", self.__rec_sample),
            ("Channels:", self.__rec_channels),
        ])
        
        sec2 = self.__create_pref_section("Record directory", [
            (None, rec_default_dir),
            ("Record directory:", self.__rec_fc),
        ])
        
        return self.__create_pref_page([sec1, sec2])
    
    #
    # callbacks for options
    #
    
    def __on_rec_default_dir_toggled(self, button):
        self.__rec_fc.set_sensitive(not button.get_active())
    
    def __on_ed_use_default_toggled(self, button):
        self.__ed_font.set_sensitive(not button.get_active())
        sced.prefs.set("Editing", "use-default-font", button.get_active())
    
    def __on_ed_font_font_set(self, button):
        sced.prefs.set("Editing", "font", button.get_font_name())
    
    #
    # callbacks for options end
    #
    
    def __create_pref_page(self, sections):
        vbox = gobject.new(gtk.VBox, spacing=18, border_width=12)
        
        for sec in sections:
            vbox.pack_start(sec, expand=False)
            sec.show()
        
        return vbox
    
    # FIXME: implement custom widget (or widget sequence) as well
    def __create_pref_section(self, title, wlabels=[], custom=[]):
        # wlabes is sequence of tuples (label, widget)
        vbox = gtk.VBox(spacing=6)
        
        label = gobject.new(gtk.Label, label="<b>%s</b>" % title,
            use_markup=True, xalign=0)
        vbox.pack_start(label, expand=False)
        label.show()
        
        align = gobject.new(gtk.Alignment, left_padding=12)
        vbox.pack_start(align, expand=False)
        align.show()
        
        table = gobject.new(gtk.Table,
            n_rows=len(wlabels) + len(custom),
            n_columns=2,
            row_spacing=6,
            column_spacing=12)
        align.add(table)
        table.show()
        
        for i in range(len(wlabels)):
            l, w = wlabels[i]
            label = gobject.new(gtk.Label, label=l, xalign=0)
            widget = w
            
            widget.connect("notify::sensitive", self.on_widget_notify_sensitive)
            widget.set_data("label", label)
            
            if l is not None:
                table.attach(label, 0, 1, i, i + 1,
                    xoptions=gtk.FILL, yoptions=gtk.FILL)
                table.attach(widget, 1, 2, i, i + 1,
                    xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.FILL)
            else:
                table.attach(widget, 0, 2, i, i + 1,
                    xoptions=gtk.EXPAND | gtk.FILL, yoptions=gtk.FILL)
        
        table.show_all()
        
        return vbox
    
    def on_widget_notify_sensitive(self, widget, spec):
        label = widget.get_data("label")
        if label is not None:
            label.set_sensitive(widget.props.sensitive)
    
    def do_response(self, response_id):
        self.hide()
        return True

    def do_delete_event(self, event):
        self.hide()
        return True
