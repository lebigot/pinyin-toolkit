#!/usr/bin/python
#-*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# This is a plugin for Anki: http://ichi2.net/anki/
# It is part of the Pinyin Toolkit plugin.
#
# This file was modifed from the HanziStats plugin inofficial versions 0.08.1b and 0.08.2.
# The plugin is now maintained as part of Pinyin Toolkit by Nick Cook and Max Bolingbroke.
# Support requests should be sent to pinyintoolkit@gmail.com.
#
# The following people have worked on the code for Hanzi Stats prior to it merge with Pintin Toolkit.
# Original Author:                    Hedge (c dot reksten dot monsen at gmail dot com)
# Hack to Reference Text Files:       Junesun (yutian dot mei at gmail dot com)
# Innofficial 0.08.2 (Traditional):   JamesStrange at yahoo dot com
#
# License:     GNU GPL
# ---------------------------------------------------------------------------

from PyQt4 import QtGui, QtCore

import hooks

from pinyin.hanzistats import hanziStats
from pinyin.logger import log


class HanziStatsHook(hooks.Hook):
    def install(self):
        log.info("Installing Hanzi statistics hook")
        
        # NB: must store reference to action on the class to prevent it being GCed
        self.action = QtGui.QAction('Hanzi Statistics by PyTK', self.mw)
        self.action.setStatusTip('Hanzi Statistics by PyTK')
        self.action.setEnabled(True)
        self.action.setIcon(QtGui.QIcon("../icons/hanzi.png"))
        
        def finish(x):
            html, python_actions = x
            self.mw.help.showText(html, py=dict([(k, lambda action=action: finish(action())) for k, action in python_actions]))
        
        self.mw.connect(self.action, QtCore.SIGNAL('triggered()'), lambda: finish(hanziStats(self.config, self.mw.deck.s)))
        self.mw.form.menuTools.addAction(self.action)
        
        log.info('Hanzi statistics plugin loaded')
