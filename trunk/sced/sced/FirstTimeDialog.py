# -*- coding: utf-8 -*-

import os.path

import gobject
import gtk

import sced

class FirstTimeDialog(gtk.Assistant):

    __gsignals__ = {
        "apply":    "override",
        "cancel":   "override",
        "close":    "override",
        "prepare":  "override",
    }

    def __init__(self, parent):
        gtk.Assistant.__init__(self)
        
        self.props.title=_("Sced setup")
        self.__parent = parent
        self.__parent.set_sensitive(False)
        self.set_transient_for(self.__parent)
        self.set_modal(True)
        self.set_position(gtk.WIN_POS_CENTER)        
        
        self.__size_group = gtk.SizeGroup(gtk.SIZE_GROUP_HORIZONTAL)
        
        self.__create_page1()
        self.__create_page2()
        self.__create_page3()
        
        #self.set_default_size(512, 384)
    
    def __create_page1(self):
        page = gobject.new(gtk.Alignment,
            xalign=0.5,
            yalign=0.5,
            xscale=0,
            yscale=0,
            border_width=12)
        #page = gtk.Alignment(0.5, 0.5)
        
        vbox = gtk.VBox(spacing=12)
        page.add(vbox)
        
        label = gobject.new(gtk.Label,
            label=_("..."),
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        vbox.pack_start(label, expand=False)
        
        label = gobject.new(gtk.Label,
            label=_("So, let's set some initial stuff."),
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        self.__size_group.add_widget(label)
        vbox.pack_start(label, expand=False)
        
        page.show_all()
        
        self.append_page(page)
        self.set_page_title (page, _("Sced setup"))
        self.set_page_complete (page, True)
        self.set_page_type (page, gtk.ASSISTANT_PAGE_INTRO)
    
    def __create_page2(self):
        page = gobject.new(gtk.Alignment,
            xalign=0.5,
            yalign=0.5,
            xscale=0,
            yscale=0,
            border_width=12)
        
        vbox = gtk.VBox(spacing=18)
        page.add(vbox)
        
        label = gobject.new(gtk.Label,
            label=_("Here you must specify, the runtime directory, where SuperCollider will store it's synth definition files (the synthdefs). Typically this is a directory, where you'll also keep your code and related files. The runtime directory must contain a <b>synthdefs</b> folder and optionally a <b>sounds</b> folder (most examples use samples from the sounds/ dir)."),
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        self.__size_group.add_widget(label)
        vbox.pack_start(label, expand=False, fill=False)
        
        hbox = gtk.HBox(spacing=12)
        vbox.pack_start(hbox)
        
        label = gtk.Label(_("Runtime directory:"))
        hbox.pack_start(label, expand=False, fill=False)
        
        self.__fc_button = gobject.new(gtk.FileChooserButton,
            title=_("Choose working directory"),
            action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER)
        hbox.add(self.__fc_button)
        self.__fc_button.connect("selection-changed",
            self.__on_filechooser_selection_changed)
        
        hbox = gtk.HBox(spacing=12)
        vbox.pack_start(hbox, expand=False)
        
        self.__warning_image = gtk.image_new_from_stock(gtk.STOCK_DIALOG_ERROR,
                                                        gtk.ICON_SIZE_DIALOG)
        hbox.pack_start(self.__warning_image, expand=False, fill=False)
        
        self.__warning_label = gobject.new(gtk.Label,
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        self.__size_group.add_widget(self.__warning_label)
        hbox.pack_start(self.__warning_label, expand=False)
        
        self.__runtimedir_page = page
        page.show_all()
        self.append_page(page)
        self.set_page_title (page, _("Working directory"))
        
        self.__update_page2()
        
        #self.set_page_complete (page, True)
        #self.set_page_type (button, gtk.ASSISTANT_PAGE_INTRO)
    
    def __create_page3(self):
        page = gobject.new(gtk.Alignment,
            xalign=0.5,
            yalign=0.5,
            xscale=0,
            yscale=0,
            border_width=12)
        
        vbox = gtk.VBox(spacing=12)
        page.add(vbox)
        
        label = gobject.new(gtk.Label,
            label=_("..."),
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        self.__size_group.add_widget(label)
        vbox.pack_start(label, expand=False)
        
        label = gobject.new(gtk.Label,
            label=_("Setup complete, ready to start."),
            justify=gtk.JUSTIFY_FILL,
            use_markup=True,
            wrap=True,
            xalign=0)
        self.__size_group.add_widget(label)
        vbox.pack_start(label, expand=False)
        
        page.show_all()
        
        self.append_page(page)
        self.set_page_title (page, "Complete")
        self.set_page_complete (page, True)
        self.set_page_type (page, gtk.ASSISTANT_PAGE_CONFIRM)
    
    def __update_page2(self):
        rdir = self.__fc_button.get_current_folder()
        
        if os.path.isdir(os.path.join(rdir, "synthdefs")):
            self.__warning_image.props.icon_name = "stock_volume-mute"
            self.__warning_label.props.label = "Yes"
            self.set_page_complete(self.__runtimedir_page, True)
        else:
            self.__warning_image.props.icon_name = "stock_volume-mute"
            self.__warning_label.props.label = "No"
            self.set_page_complete(self.__runtimedir_page, False)
    
    def __on_filechooser_selection_changed(self, *args):
        self.__update_page2()
    
    def do_apply(self):
        rdir = self.__fc_button.get_current_folder()
        sced.prefs.set("General", "runtime-dir", rdir)
        self.__parent.set_sensitive(True)
        self.__parent["RestartLang"].activate() # FIXME: only if user wishes so
    
    def do_cancel(self):
        gtk.main_quit()
    
    def do_close(self):
        self.destroy()
    
    def do_prepare(self, page):
        #page = self.get_nth_page(self.get_current_page())
        #self.set_title(assistant.get_page_title(page))
        pass
