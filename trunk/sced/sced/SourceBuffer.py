#-*- coding: utf-8 -*-

import os

import gobject
import pango
import gtksourceview

import sced

class SourceBuffer(gtksourceview.SourceBuffer):

    # FIXME: del untitled number from instance one title is set
    untitled_numbers = []

    __gsignals__ = {
            "title-updated":
                (gobject.SIGNAL_RUN_LAST,
                 gobject.TYPE_NONE, ()),
    } # __gsignals__
    
    def __init__(self, filename=None):
        gtksourceview.SourceBuffer.__init__(self)
        self.filename = None

        # FIXME: supercollider by default for now
        lang = sced.lang_manager.get_language_from_mime_type("text/x-sc")
        
        self.props.language = lang
        self.props.highlight = True
        
        if filename is None:
            self.__untitled_number = 1
            while self.__untitled_number in SourceBuffer.untitled_numbers:
                self.__untitled_number += 1
            SourceBuffer.untitled_numbers.append(self.__untitled_number)
        else:
            self.load(filename)
    
    def load(self, filename):
        self.begin_not_undoable_action()
        code = open(filename).read()
        
        self.set_text(code)
        self.set_modified(False)
        
        self.end_not_undoable_action()
        
        self.place_cursor(self.get_start_iter())
        self.set_modified(False)
        
        self.filename = filename
        # FIXME: this is awkward
        try:
            self.__untitled_number
            SourceBuffer.untitled_numbers.remove(self.__untitled_number)
        except:
            pass
        self.emit("title-updated")
    
    def save(self, filename, copy=False):
        code = self.props.text
        f = open(filename, 'w')
        f.write(code)
        f.close()
        if not copy:
            self.set_modified(False)
            if filename != self.filename:
                self.emit("title-updated")
            self.filename = filename
            # FIXME: this is awkward
            try:
                self.__untitled_number
                SourceBuffer.untitled_numbers.remove(self.__untitled_number)
            except:
                pass
            self.emit("title-updated")
    
    def get_title(self):
        if self.filename is not None:
            return os.path.basename(self.filename)
        else:
            return _("Untitled %d") % self.__untitled_number
    
    def find_block(self, where=None):
        # if nowhere, select from cursor
        if where is None:
            iter1 = self.get_iter_at_mark(self.get_insert())
            where = iter1.copy()
        else:
            iter1 = where.copy()
        
        # find first opening bracket
        while True:
            iter1.set_line_offset(0)
            
            iter2 = iter1.copy()
            iter2.forward_to_line_end()
            
            if sced.is_block_beginning(self.get_text(iter1, iter2)):
                break
            
            if not iter1.backward_line():
                raise RuntimeError, "Block not found!"
        
        iter2 = iter1.copy()
        count = 1
        
        while True:
            if not iter2.forward_char():
                raise RuntimeError, "Block not found!"

            if iter2.get_char() == "(":
                count += 1
            elif iter2.get_char() == ")":
                count -= 1
            
            if count == 0:
                break
        
        # include closing bracket and the following character
        # for proper behaviour of in_range below!
        iter2.forward_chars(2) 
        
        if where.in_range(iter1, iter2):
            return iter1, iter2
        else:
            raise RuntimeError, "Block not found!"
    
    # these should preserve space before line
    def comment_lines(self, iter1=None, iter2=None):
        if iter1 is None:
            iter1 = self.get_iter_at_mark(self.get_insert())
            iter1.set_line_offset(0)
        if iter2 is None:
            iter2 = iter1.copy()
            iter2.set_line_offset(0)
        # pass

    # these should preserve space before line
    def uncomment_lines(self, iter1=None, iter2=None):
        pass
