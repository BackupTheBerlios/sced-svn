# -*- coding: utf-8 -*-

import os
# used to sleep during "record" command delay
import time

import gobject
import pango
import gtk

import sced

# connect buffer events (cursor, changed, modified-changed, here in the window
# remove "set_modified" everywhere (except quitting), this is now in the buffer

#
# FIXME: FIXME: FIXME:
# need to optimize update_ui ()!!!
# it does too many things and is a bottleneck!!!
# -->
# * split it in several routines, which are individiually called from actions
# * use modiefied-changed handler
# --> does this signal get emitted when i use "set_modified"? likely, yes.
# --> is switch page called when last page is destroyed? NO!.

# ALSO:
# the "complete update_ui" in "switch_page" makes many, many ui updates
# unneccessary // open?, close?, etc.?

# when loading files:
# 1. FIRST load text into buffer
# 2. THEN set text to the newly created page
# --> to avoid loading empty pages in case of error

# FIXME: FIXME: FIXME:
# make a new function to create pages
# (and remove "New".activate() from all loadings

# closeall shows the same confirmation dialog as quit
#

# as for "documents-save-all"...
# * switch to all childs and activate "Save"
# * then switch back to last active child (gedit actually does something like that)

class Window(gtk.Window):

    __gsignals__ = {
        "delete-event": "override",
    }
    
    # FIXME: separate ui and logic stuff in the constructyor
    def __init__(self, filenames=[]):
        gtk.Window.__init__(self)
        self.__actions = {}
        self.__register_stock()
        self.__clipboard = gtk.clipboard_get()
        self.__recent_manager = gtk.recent_manager_get_default()
        self.__preferences_dialog = None

        self.__ui = gtk.UIManager()
        self.__ui.connect("actions-changed", self.__on_ui_actions_changed)
        self.__ui.connect("connect-proxy", self.__on_ui_connect_proxy)

        group = self.__create_actions()
        self.__ui.insert_action_group(group, 0)
        self.__ui.add_ui_from_file("sced-ui.xml")
        
        self.add_accel_group(self.__ui.get_accel_group())
        
        vbox = gtk.VBox()
        self.add(vbox)
        vbox.show()
        
        # menubar
        menubar = self.__ui.get_widget("/Menubar")
        vbox.pack_start(menubar, expand = False)
        menubar.show()

        # toolbar
        toolbar = self.__ui.get_widget("/Toolbar")
        vbox.pack_start(toolbar, expand = False)
        toolbar.show()

        # paned
        vpaned = gobject.new(gtk.VPaned, position=500)
        vbox.pack_start(vpaned)
        vpaned.show()

        # notebook
        self.__notebook = gobject.new(gtk.Notebook, scrollable=True)
        vpaned.pack1(self.__notebook)
        self.__notebook.show()
        
        # logview
        self.__log_view = sced.LogView()
        vpaned.pack2(self.__log_view, resize=False)
        self.__log_view.show()

        # statusbar
        self.__statusbar = sced.Statusbar()
        vbox.pack_start(self.__statusbar, expand = False)
        self.__statusbar.show()

        # recent chooser
        recent_menu = gtk.RecentChooserMenu(self.__recent_manager)
        menuitem = self.__ui.get_widget("/Menubar/FileMenu/RecentFiles/RecentMenu")
        menuitem.set_submenu(recent_menu)
        
        recent_menu.connect("item-activated", self.recent_activated)

        # for geometry, toolbar, statusbar
        self.__load_preferences()

        self.__notebook.connect_after("switch-page", self.__on_notebook_switch_page)
        self.__notebook.connect_after("remove", self.__on_notebook_page_removed)

        self.__lang = sced.Lang()
        #self.__source_folder = None
        
        if filenames == []:
            self["New"].activate()
        else:
            for f in filenames:
                self.__load_file(f)
        
        self.__update_full()
        
        # FIXME: this stops server, not launched from here
        if sced.prefs.get("General", "runtime-dir") != "":
            self["RestartLang"].activate()

    def __getitem__(self, name):
        return self.__actions[name]
    
    def __load_preferences(self):
        self.props.default_width = sced.prefs.get("Geometry", "width")
        self.props.default_height = sced.prefs.get("Geometry", "height")
        
        self["ViewToolbar"].set_active(sced.prefs.get("General", "toolbar-visible"))
        self["ViewStatusbar"].set_active(sced.prefs.get("General", "statusbar-visible"))
        self["ViewLog"].set_active(sced.prefs.get("General", "output-visible"))
    
    def __register_stock(self):
        items = [
            # last arg is translation domain
            ("scedit-stop-sound", _("Stop Sound"), 0, 0, "sced"),
        ]

        source = gtk.IconSource()
        source.set_icon_name("stock_volume-mute")

        set = gtk.IconSet()
        set.add_source(source)

        factory = gtk.IconFactory()
        factory.add_default()
        factory.add("scedit-stop-sound", set)

    def __create_actions(self):
        entries = (
            ("FileMenu",            None, _("_File")),
            ("EditMenu",            None, _("_Edit")),
            ("ViewMenu",            None, _("_View")),
            ("SearchMenu",          None, _("_Search")),
            ("LanguageMenu",        None, _("_Language")),
            ("ServerMenu",          None, _("_Server")),
            ("DocumentsMenu",       None, _("_Documents")),
            ("HelpMenu",            None, _("_Help")),
            
            ("RecentMenu",          None, _("Recently used")),

            # file

            ("New", gtk.STOCK_NEW, _("_New"), "<control>N",
            _("Create a new file"), self.on_new),

            ("Open", gtk.STOCK_OPEN, _("_Open..."), "<control>O",
            _("Open an existing file"), self.on_open),
            
            ("Save", gtk.STOCK_SAVE, _("_Save"), "<control>S",
            _("Save the current file"), self.on_save),

            ("SaveAs", gtk.STOCK_SAVE, _("Save _As..."), "<shift><control>S",
            _("Save the current file with a new name"), self.on_save_as),

            # FIXME: a better tooltip
            ("SaveCopy", None, _("Sa_ve A Copy..."), None,
            _("Save a copy of the current file"), self.on_save_a_copy),

            ("Revert", gtk.STOCK_REVERT_TO_SAVED, _("_Revert"), None,
            _("Revert to previously saved version"), self.on_revert),

            ("PageSetup", None, _("Page Set_up..."), None,
            _("Setup page"), None),

            ("PrintPreview", gtk.STOCK_PRINT_PREVIEW, _("Print Previe_w..."),
             "<shift><control>P", _("Print preview current source"), None),

            ("Print", gtk.STOCK_PRINT, _("_Print..."), "<control>P",
            _("Print current source"), None),

            ("Close", gtk.STOCK_CLOSE, _("_Close"), "<control>W",
            _("Close the current file"), self.on_close),

            ("Quit", gtk.STOCK_QUIT, _("_Quit"), "<control>Q",
            _("Quit the application"), self.on_quit),

            # edit

            ("Undo", gtk.STOCK_UNDO, _("_Undo"), "<control>Z",
            _("Undo the effect of the previous action"), self.on_undo),

            ("Redo", gtk.STOCK_REDO, _("_Redo"), "<control><shift>Z",
            _("Redo the undone action"), self.on_redo),

            ("Cut", gtk.STOCK_CUT, _("Cu_t"), "<control>X",
            _("Cut the selection"), self.on_cut),

            ("Copy", gtk.STOCK_COPY, _("_Copy"), "<control>C",
            _("Copy the selection"), self.on_copy),

            ("Paste", gtk.STOCK_PASTE, _("_Paste"), "<control>V",
            _("Paste clipboard contents"), self.on_paste),

            ("Delete", gtk.STOCK_DELETE, _("Delete"), "Delete",
            _("Remove the selected text"), self.on_delete),

            ("SelectAll", None, _("Select _All"), "<control>A",
            _("Select"), self.on_select_all),

            ("SelectBlock", None, _("Select Block"), "<control>B",
            _("Select current code block"), self.on_select_block),

            ("Comment", None, _("Comment"), "<control>slash",
            _("Comment current line or selection"), self.on_comment),

            ("Uncomment", None, _("Uncomment"), "<control><shift>slash",
            _("Uncomment current line or selection"), self.on_uncomment),

            ("Indent", gtk.STOCK_INDENT, _("Indent"), "<control>T",
            _("Indent current line or selection"), self.on_indent),

            ("Unindent", gtk.STOCK_UNINDENT, _("Unindent"), "<control><shift>T",
            _("Unindent current line or selection"), self.on_unindent),

            ("Preferences", gtk.STOCK_PREFERENCES, _("Pr_eferences..."), None,
            _("Change application preferences"), self.on_preferences),

            # search

            ("Find", gtk.STOCK_FIND, _("_Find..."), "<control>F",
            _("Search for text"), self.on_find),

            ("FindNext", gtk.STOCK_FIND, _("Find Ne_xt"), "<control>G",
            _("Search forward"), None),

            ("FindPrevious", gtk.STOCK_FIND, _("Find Pre_vious"), "<shift><control>G",
            _("Select"), None),

            ("Replace", gtk.STOCK_FIND_AND_REPLACE, _("R_eplace..."), "<control>H",
            _("Select"), None),

            ("GotoLine", gtk.STOCK_JUMP_TO, _("Go to _Line..."), "<control>I",
            _("Select"), self.on_goto_line),

            # lang

            ("Evaluate", None, _("_Evaluate"), "<control>E",
            _("Evaluate current line or selection"), self.on_evaluate),

            ("EvaluateAll", gtk.STOCK_EXECUTE, _("_Evaluate All"), "<shift><control>E",
            _("Evaluate the entire buffer"), self.on_evaluate_all),
            
            ("RecompileLibrary", gtk.STOCK_REFRESH, _("Recompile Library"), None,
            _("Recompile class library"), None),
            
            ("RestartLang", None, _("_Restart Interpreter"), None,
            _("Restart underrunning sclang"), self.on_restart_lang),

            ("ClearLog", gtk.STOCK_CLEAR, _("Clear _Log"), None,
            _("Clear the log"), self.on_clear_log),

            # serv

            ("StartServer", None, _("Start Server"), None,
            _("Start server"), self.on_start_server),

            ("StopServer", None, _("Stop Server"), None,
            _("Stop server"), self.on_stop_server),
            
            # FIXME: not scedit, but sced
            ("StopSound", "scedit-stop-sound", _("_Stop sound"), "Escape",
            _("Stop sound and free all server nodes"), self.on_stop_sound),

            # Documents

            ("SaveAll", gtk.STOCK_SAVE, _("Save All"), "<shift><ctrl>L",
            _("Save all open files"), self.on_save_all),

            ("CloseAll", gtk.STOCK_CLOSE, _("Close All"), "<shift><ctrl>W",
            _("Close all open files"), self.on_close_all),

            # Help

            ("Help", gtk.STOCK_HELP, _("_Contents"), "F1",
            _("Help"), self.on_help),

            ("FindReference", gtk.STOCK_INDEX, _("_Get Reference"), "<shift>F1",
            _("Get reference for klass under cursor"), None),

            ("About", gtk.STOCK_ABOUT, _("_About Sced"), None,
            _("About this application"), self.on_about),
        )

        toggle_entries =(
            ("ViewToolbar", None, "_Toolbar", None,
             _("Show or hide the toolbar"), self.on_view_toolbar, True),

            ("ViewStatusbar", None, "_Statusbar", None,
             _("Show or hide the statusbar"), self.on_view_statusbar, True),

            ("ViewLog", None, "_Log", "<control><alt>O",
             _("Show or hide the log"), self.on_view_log, True),

            ("Record", gtk.STOCK_MEDIA_RECORD, "_Record", "<control>R",
             _("Toggle recording server output"), self.on_record, False),
        )

        group = gtk.ActionGroup("Actions")
        
        group.add_actions(entries)
        group.add_toggle_actions(toggle_entries)
        
        return group
    
    # disable Revert if no filename
    def __update_buffer_actions(self, sensitive):
        # FIXME: recreate this list
        li = [
            "Save",         "SaveAs",       "SaveCopy",         "Revert",
            "PrintPreview", "Print",        "Close",

            "Undo",         "Redo",
            "Cut",          "Copy",         "Paste",            "Delete",

            "SelectAll",    "SelectBlock",
            "Comment",      "Uncomment",    "Indent",          "Unindent",

            "Find",         "FindNext",     "FindPrevious",
            "Replace",      "GotoLine",

            "Evaluate",     "EvaluateAll",
            "SaveAll",      "CloseAll",

            # FIXME: "GetReference"?
        ]
        
        [self[action].set_sensitive(sensitive) for action in li]
    
    # currently not used, lang does not fail right now
    def __update_lang_actions(self, sensitive):
        li = [
            "Evaluate",     "EvaluateAll",
            "StartServer",  "StopServer",
            "Record",       "StopSound",
        ]
        
        [self[action].set_sensitive(sensitive) for action in li]
    
    # FIXME: include label update as well (what's that?)
    def __update_title(self):
        if self.__active_page == None:
            self.set_title("Sced")
            return
        
        filename = self.__active_page.buffer.get_title()
        
        if self.__active_page.buffer.get_modified():
            self.set_title("*" + filename + " - Sced")
        else:
            self.set_title(filename + " - Sced")
    
    def __update_full(self):
        self.__update_title()
        
        # FIXME: put this into other place
        self.__statusbar.props.cursor_pos_visible = self.__active_page is not None
        self.__statusbar.props.overwrite_visible = self.__active_page is not None
        
        # FIXME: decide, where to put THIS:
        if self.__active_page is None:
            self.__update_buffer_actions(False)
            self.set_title("Sced")
            return
        else:
            self.__update_ui() # FIXME: replace
            self.__update_buffer_actions(True)
    
    def __update_ui(self):
        # undo, redo
        buffer = self.__active_page.buffer
        self["Undo"].set_sensitive(buffer.can_undo())
        self["Redo"].set_sensitive(buffer.can_redo())
        
        self.__statusbar.set_overwrite(self.__active_page.view.props.overwrite)
    
    # FIXME: last closed page will preserve it's dir, and only as fallback choose workdir
    def __get_current_sourcedir(self):
        default = sced.prefs.get("General", "runtime-dir")
        
        if self.__active_page is None:
            return default
        
        buffer = self.__active_page.buffer
        if buffer.filename is None:
            return default
        
        return os.path.dirname(buffer.filename)

    # action handlers

    def on_new(self, action):
        page = self.create_page()
        self.__notebook.props.page = self.__notebook.page_num(page)
        
        # FIXME: bad to do this here?
        # --> but where, Container.add signal won't work
        #self.__update_buffer_actions(True)
        self.__update_full()

    def on_open(self, action):
        dialog = sced.FileChooserDialog(title=_("Open File..."),
            parent=self,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_OPEN, gtk.RESPONSE_OK))

        dialog.set_current_folder(self.__get_current_sourcedir())
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            self.load_file(filename)
        
        dialog.destroy()
        self.__update_full()
    
    # FIXME: bad, bad, better write save_file thingie
    def on_save(self, action):
        filename = self.__active_page.buffer.filename
        if filename is None:
            self["SaveAs"].activate()
        else:
            self.__active_page.buffer.save(filename)
            self.__update_ui()

            # add recent
            # FIXME: cleanup this
            self.__recent_manager.add_full("file://" + filename,
                {
                    "mime_type": "text/x-sc",
                    "app_name": "Sced",
                    "app_exec": "sced.py"
                })
    
    # FIXME: bad, bad, better write save_file thingie
    def on_save_as(self, action):
        #if self.__active_page.sourcedir is None:
        #       self.__active_page.sourcedir = os.getcwd()
        dialog = sced.FileChooserDialog(title=_("Save As..."),
            parent=self,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_SAVE, gtk.RESPONSE_OK))
        dialog.props.do_overwrite_confirmation = True
        
        dialog.set_current_folder(self.__get_current_sourcedir())
        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            
            self.__active_page.buffer.filename = filename
            self["Save"].activate()

            # add recent
            # FIXME: cleanup this
            self.__recent_manager.add_full("file://" + filename,
                {
                    "mime_type": "text/x-sc",
                    "app_name": "Sced",
                    "app_exec": "sced.py"
                })

        dialog.destroy()

    def on_save_a_copy(self, action):
        dialog = sced.FileChooserDialog(title=_("Save A Copy..."),
            parent=self,
            action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                     gtk.STOCK_SAVE, gtk.RESPONSE_OK))

        dialog.set_current_folder(self.__get_current_sourcedir())

        dialog.set_default_response(gtk.RESPONSE_OK)
        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            filename = dialog.get_filename()
            try:
                open(filename, "w").write(self.__active_page.buffer.props.text)
            except Exception, e:
                print "Could not save a copy!", e

        dialog.destroy()

    def on_revert(self, action):
        dialog = gtk.MessageDialog(parent=self,
            flags=gtk.DIALOG_MODAL,
            type=gtk.MESSAGE_QUESTION,
            message_format=_("Revert the file to its saved state?"))

        dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
        dialog.add_button(gtk.STOCK_REVERT_TO_SAVED, gtk.RESPONSE_OK)
        dialog.format_secondary_markup("All changes will be lost")

        response = dialog.run()

        if response == gtk.RESPONSE_OK:
            # reload
            pass

        dialog.destroy()
    
    #
    # recent
    #
    
    def recent_activated(self, chooser):
        filename = sced.uri_to_local(chooser.get_current_uri())
        #buffer = sced.SourceBuffer(filename)
        self.load_file(filename)
    
    #
    # printing
    # 
    
    # ...
    
    def on_close(self, action):
        buffer = self.__active_page.buffer

        if buffer.get_modified():
            dialog = gtk.MessageDialog(parent = self,
                    flags = gtk.DIALOG_MODAL,
                    type = gtk.MESSAGE_WARNING,
                    message_format = _("Save changes before closing?"))

            dialog.add_button(gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
            dialog.add_button(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL)
            dialog.add_button(gtk.STOCK_SAVE, gtk.RESPONSE_OK)

            dialog.format_secondary_markup("If you don't save, ..")

            dialog.set_default_response(gtk.RESPONSE_OK)
            response = dialog.run()

            dialog.destroy()

            if response == gtk.RESPONSE_OK:
                self["Save"].activate()
                #num = self.__notebook.page_num(self.__active_page)
                #self.__notebook.remove_page(num)
            elif response != gtk.RESPONSE_CLOSE:
                return

        #num = self.__notebook.props.page
        #self.__notebook.remove_page(num)
        self.__notebook.remove(self.__active_page)
        self.__update_full()

    # FIXME: need a method like "close page" here
    def on_quit(self, action):
        unsaved = []
        for page in self.__notebook.get_children():
            if page.buffer.get_modified():
                unsaved.append(page)

        if len(unsaved) == 1:
            # FIXME: "close once"
            self["Close"].activate()
            if self.__active_page is None:
                self["Quit"].activate()

        elif len(unsaved) > 1:
            # FIXME: many
            dialog = sced.QuitConfirmationDialog(self, unsaved)
            response = dialog.run()
            #saved = dialog.get_saved()
            dialog.destroy()

            if response == gtk.RESPONSE_CLOSE:
                [page.buffer.set_modified(False) for page in unsaved]
                self["Quit"].activate()
            elif response == gtk.RESPONSE_OK:
                print "to save yet"
            else:
                pass

        elif len(unsaved) == 0:
            self["StopServer"].activate()
            self.__lang.stop()
            
            # FIXME: only if save geometry on exit
            w, h = self.get_allocation().width, self.get_allocation().height
            sced.prefs.set("Geometry", "width", w)
            sced.prefs.set("Geometry", "height", h)
            
            gtk.main_quit()

    # edit

    # FIXME: update ui where neeeded

    def on_undo(self, action):
        self.__active_page.buffer.undo()
        # FIXME: update actions
        # FIXME: update title
        self.__update_ui()

    def on_redo(self, action):
        self.__active_page.buffer.redo()
        self.__update_ui()

    def on_cut(self, action):
        clipboard = self.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD)
        self.__active_page.buffer.cut_clipboard(clipboard,
            self.__active_page.view.get_editable())

    def on_copy(self, action):
        clipboard = self.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD)
        self.__active_page.buffer.copy_clipboard(clipboard)

    def on_paste(self, action):
        clipboard = self.get_clipboard(gtk.gdk.SELECTION_CLIPBOARD)
        self.__active_page.buffer.paste_clipboard(clipboard,
            None, self.__active_page.view.get_editable())

    def on_delete(self, action):
        buffer = self.__active_page.buffer
        if not buffer.get_selection_bounds():
            mark = buffer.get_insert()
            iter1 = buffer.get_iter_at_mark(mark)
            iter2 = iter1.copy()
            iter2.forward_char()
            buffer.delete_interactive(iter1, iter2,
                    self.__active_page.view.get_editable())
        else:
            buffer.delete_selection(True,
                self.__active_page.view.get_editable())

    def on_select_all(self, action):
        first, last = self.__active_page.buffer.get_bounds()
        self.__active_page.buffer.select_range(first, last)

    def on_select_block(self, action):
        start, end = self.__active_page.buffer.find_block()
        self.__active_page.buffer.select_range(start, end)
    
    def on_comment(self, action):
        # these should preserve space before line
        pass

    def on_uncomment(self, action):
        # these should preserve space before line
        pass

    def on_indent(self, action):
        # these should unindent backwards if no more whitespace
        pass

    def on_unindent(self, action):
        pass

    def on_preferences(self, action):
        if self.__preferences_dialog is None:
            self.__preferences_dialog = sced.PreferencesDialog(parent=self)
        self.__preferences_dialog.show()
    
    # view

    def on_view_toolbar(self, action):
        visible = action.get_active()
        self.__ui.get_widget("/Toolbar").props.visible = visible
        sced.prefs.set("General", "toolbar-visible", visible)

    def on_view_statusbar(self, action):
        visible = action.get_active()
        self.__statusbar.props.visible = action.get_active()
        sced.prefs.set("General", "statusbar-visible", visible)

    def on_view_log(self, action):
        visible = action.get_active()
        if visible:
            self.__log_view.show()
        else:
            self.__log_view.hide()
        sced.prefs.set("General", "output-visible", visible)

    # search

    def on_find(self, action):
        #dialog = SearchDialog(self)
        #dialog.show()
        pass

    def on_goto_line(self, action):
        dialog = sced.GotoLineDialog(self)
        dialog.run()
        dialog.destroy()

    # lang

    def on_evaluate(self, action):
        buffer = self.__active_page.buffer
        try:
            iter1, iter2 = buffer.get_selection_bounds()
        except ValueError:
            iter1 = buffer.get_iter_at_mark(buffer.get_insert())
            iter1.set_line_offset(0)

            iter2 = iter1.copy()
            iter2.forward_to_line_end()
            
            # evaluate block, if parenthesis is the only character in line
            if sced.is_block_beginning(buffer.get_text(iter1, iter2)):
                iter1, iter2 = buffer.find_block(iter1)
                buffer.select_range(iter1, iter2)

        text = buffer.get_text(iter1, iter2)
        self.__lang.evaluate(text)

    def on_evaluate_all(self, action):
        self.__lang.evaluate(self.__active_page.buffer.props.text)

    def on_restart_lang(self, action):
        # FIXME: make an "if"
        #self["StopServer"].activate()
        
        if self.__lang.running():
            self.__lang.stop()
        
        try:
            self.__lang.start()
        except Exception, e:
            dialog = gtk.MessageDialog(parent=self,
                flags=gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_ERROR,
                message_format="Error starting sclang")
            dialog.format_secondary_markup(str(e))
            dialog.run()
            dialog.destroy()
            return
        self.__logger = sced.Logger(self.__lang.stdout, self.__log_view)
        # FIXME: make an "if"
        #self["StartServer"].activate()

    def on_clear_log(self, action):
        start, end = self.__log_view.buffer.get_bounds()
        self.__log_view.buffer.delete(start, end)

    # serv

    # FIXME: these actions should remember last server
    # -->(s = Server.local.boot)
    def on_start_server(self, action):
        self.__lang.evaluate("Server.local.boot;", silent=True)

    def on_stop_server(self, action):
        # FIXME: do only if server running...
        try:
            self.__lang.evaluate("Server.local.quit;", silent=True)
        except:
            print ">> attempted to stop non-running server (lang)"

    def on_record(self, action):
        self.__lang.toggle_recording(action.get_active())
    
    def on_stop_sound(self, action):
        if self["Record"].get_active():
            self["Record"].activate() # untoggle
        self.__lang.stop_sound()

    def on_save_all(self, action):
        current_page = self.__active_page
        for page in self.__notebook.get_children():
            if page.buffer.get_modified():
                pass

    def on_close_all(self, action):
        pass

    # help

    def on_help(self, action):
        passl
    
    def on_get_refenence(self, action):
        pass

    def on_about(self, action):
        dialog = gobject.new(gtk.AboutDialog,
                authors     = ["Артём Попов <artfwo@gmail.com>"],
                comments    = _("SuperCollider editing environment."),
                copyright   = "Copyright © 2006 Артём Попов <artfwo@gmail.com>",
                license     = "GPL",
                #logo        = gtk.gdk.pixbuf_new_from_file("logo.png"),
                name        = "Sced",
                version     = 0.1)
        dialog.set_transient_for(self)
        dialog.run()
        dialog.destroy()
    
    #
    # load file
    #
    
    def create_page(self, buffer=None):
        if buffer is None:
            buffer = sced.SourceBuffer ()
        
        page = sced.SourcePage(buffer)
        label = sced.SourcePageLabel(page)

        page.connect("update-ui", self.__on_source_page_update_ui)
        page.connect("update-cursor", self.__on_source_page_update_cursor)

        num = self.__notebook.append_page(page, label)
        self.__notebook.set_tab_reorderable(page, True)
        page.show()
        
        #self.__notebook.set_current_page(num)
        page.view.grab_focus()
        #self.__update_ui() # FIXME: move/remove this

        label.connect("close-button-clicked",
            self.__on_page_close_button_clicked, page)
        
        # FIXME: bad to do this here?
        # --> but where, Container.add signal won't work
        # self.__update_buffer_actions(True)
        
        return page
    
    def load_file(self, filename):
        if self.__active_page is None:
            page = self.create_page(sced.SourceBuffer(filename))
            self.__notebook.props.page = self.__notebook.page_num(page)
        else:
            buffer = self.__active_page.buffer
            if buffer.props.text == "" and (not buffer.get_modified()) and \
                buffer.filename is None:
               buffer.load(filename)
            else:
                page = self.create_page(sced.SourceBuffer(filename))
                self.__notebook.props.page = self.__notebook.page_num(page)
        
        self.__recent_manager.add_full(sced.local_to_uri(filename), {
            "mime_type": "text/x-sc",
            "app_name": "Sced",
            # FIXME: app_exec must be correct
            "app_exec": "sced.py" })
        
    
    # notebook events

    # FIXME: handled two times on startup (or if no pages)
    # --> is not handled on closing last
    # --> so it's good for updatin window title
    def __on_notebook_switch_page(self, notebook, page, page_num):
        self.__active_page = self.__notebook.get_nth_page(page_num)
        # should:
        # 1. update title
        # 2. update cursor
        # 3. update undo/redo, search, etc
        # --> each buffer will have a search associated with it
        
        # new code:
        self.__update_full()
        #self.__update_ui()
    
    def __on_notebook_page_removed(self, notebook, page):
        if not notebook.get_n_pages():
            self.__active_page = None
        self.__update_full()
    
    def __on_page_close_button_clicked(self, label, page):
        if self.__active_page is page:
            self["Close"].activate()
            return

        orig_page = self.__active_page
        page_num = self.__notebook.page_num(page)
        self.__notebook.props.page = page_num
        self["Close"].activate()

        page_num = self.__notebook.page_num(orig_page)
        self.__notebook.props.page = page_num

    # source event

    def __on_source_page_update_ui(self, *args):
        self.__update_ui()

    def __on_source_page_update_cursor(self, page, line, col):
        self.__statusbar.set_position(line, col)
        #self.__update_cursor()

    # ui manager

    def __on_ui_actions_changed(self, ui):
        self.__actions.clear()
        for group in ui.get_action_groups():
            for action in group.list_actions():
                self.__actions[action.get_name()] = action

    def __on_ui_connect_proxy(self, ui, action, widget):
        if isinstance(widget, gtk.MenuItem):
            widget.connect("select", self.__on_menuitem_select, action)
            widget.connect("deselect", self.__on_menuitem_deselect, action)

    def __on_menuitem_select(self, item, action):
        if not item.get_submenu():
            id = self.__statusbar.get_context_id("tooltips")
            self.__statusbar.push(id, action.props.tooltip)

    def __on_menuitem_deselect(self, item, action):
        if not item.get_submenu():
            id = self.__statusbar.get_context_id("tooltips")
            self.__statusbar.pop(id)

    # window events

    def do_delete_event(self, event):
        self["Quit"].activate()
        return True
