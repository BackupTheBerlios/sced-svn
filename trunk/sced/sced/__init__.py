# -*- coding: utf-8 -*-

from FileChooserDialog          import FileChooserDialog
from FirstTimeDialog            import FirstTimeDialog
from GotoLineDialog             import GotoLineDialog
from Lang                       import Lang
from Logger                     import Logger
from LogView                    import LogView
from PreferencesDialog          import PreferencesDialog
from QuitConfirmationDialog     import QuitConfirmationDialog
from SourceBuffer               import SourceBuffer
from SourcePage                 import SourcePage
from SourcePageLabel            import SourcePageLabel
from Statusbar                  import Statusbar
from Window                     import Window

(REC_FORMAT_AIFF,
 REC_FORMAT_WAV,
 REC_FORMAT_AU,
 REC_FORMAT_IRCAM,
 REC_FORMAT_RAW) = range(5)

(REC_SAMPLE_8BIT,
 REC_SAMPLE_16BIT,
 REC_SAMPLE_32BIT,
 REC_SAMPLE_FLOAT,
 REC_SAMPLE_DOUBLE,
 REC_SAMPLE_MULAW,
 REC_SAMPLE_ALAW) = range(7)

import Preferences
prefs = Preferences.Preferences()
settings = prefs

import gtksourceview
lang_manager = gtksourceview.SourceLanguagesManager()
del gtksourceview

def is_block_beginning(s):
    s = "".join(s.split())
    
    # FIXME: needs further work
    if s == "(" or s.startswith("(//") or s.startswith("(/*"):
        return True
    else:
        return False

def uri_to_local(uri):
    if uri.startswith("file://"):
        return uri[7:]
    else:
        raise RuntimeError, "Unsupported URI!"

def local_to_uri(local):
    return "file://" + local
