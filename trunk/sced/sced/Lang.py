# -*- coding: utf-8 -*-

import subprocess
import time

import sced

class Lang:
    def __init__(self):
        self.__sclang = None

    def start (self):
        if self.running():
            return
        self.__sclang = subprocess.Popen(["sclang",
                "-d", sced.prefs.get("General", "runtime-dir")],
                bufsize=0,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=True)
        self.stdout = self.__sclang.stdout
        self.stdin = self.__sclang.stdin

    def stop(self):
        if self.running():
            self.stdin.close()
            self.__sclang.wait()
            self.__sclang = None

    def running(self):
        return (self.__sclang is not None) and (self.__sclang.poll () is None)

    def evaluate(self, code, silent=False):
        self.stdin.write (code)
        if silent:
            self.stdin.write ("\x1b")
        else:
            self.stdin.write ("\x0c")
        self.stdin.flush ()
    
    def toggle_recording(self, record):
        if record:
            self.evaluate("s.prepareForRecord;", silent=True)
            time.sleep(0.1) # give server some time to prepare
            self.evaluate("s.record;", silent = True)
        else:
            self.evaluate("s.stopRecording;", silent=True)
    
    def stop_sound(self):
        self.evaluate("Server.freeAll;", silent=True)
        self.evaluate("SystemClock.clear;", silent=True)
        self.evaluate("AppClock.clear;", silent=True)
        self.evaluate("TempoClock.default.clear;", silent=True)
        self.evaluate("CmdPeriod.clear;", silent=True)
        self.evaluate("Server.resumeThreads;", silent=True)
