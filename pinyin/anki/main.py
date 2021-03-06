#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil

import aqt.addons

from anki.hooks import wrap
from aqt.qt import QDialog

from pinyin.db import *
import pinyin.db.builder
import pinyin.forms.builddb
import pinyin.forms.builddbcontroller
import pinyin.updater

import hooks
import mediamanager
import notifier

import statsandgraphs

from pinyin.config import getconfig
from pinyin.logger import log

hookbuilders = hooks.hookbuilders + [
    #statsandgraphs.HanziGraphHook
  ]

class PinyinToolkit(object):
    def __init__(self, mw):
        # Right, this is more than a bit weird. The basic issue is that if we were
        # to just initialize() RIGHT NOW then we will hold the Python import lock,
        # because Anki __import__s its plugins. This ABSOLUTELY KILLS us when we
        # come to e.g. build the database on a background thread, because that code
        # naturally wants to import some stuff, but it doesn't hold the lock!
        #
        # To work around this issue, we carefully schedule initialization (and database
        # construction) for a time when Anki will not have caused us to hold the import lock.
        #
        # Debugging this was a fair bit of work!
        from anki.hooks import addHook
        #addHook("init", lambda: self.initialize(mw))
        self.initialize(mw)
    
    def initialize(self, mw):
        log.info("Pinyin Toolkit is initializing")
        
        # Build basic objects we use to interface with Anki
        thenotifier = notifier.AnkiNotifier()
        themediamanager = mediamanager.AnkiMediaManager(mw)
        
        # Open up the database
        if not self.tryCreateAndLoadDatabase(mw, thenotifier):
            # Eeek! Database building failed, so we better turn off the toolkit
            log.error("Database construction failed: disabling the Toolkit")
            return

        # Build the updaters
        updaters = {
            'expression' : pinyin.updater.FieldUpdaterFromExpression(thenotifier, themediamanager),
            'reading'    : pinyin.updater.FieldUpdaterFromReading(),
            'meaning'    : pinyin.updater.FieldUpdaterFromMeaning(),
            'audio'      : pinyin.updater.FieldUpdaterFromAudio(thenotifier, themediamanager)
          }
        
        # Finally, build the hooks.  Make sure you store a reference to these, because otherwise they
        # get garbage collected, causing garbage collection of the actions they contain
        self.hooks = [hookbuilder(mw, thenotifier, themediamanager, updaters) for hookbuilder in hookbuilders]
        for hook in self.hooks:
            hook.install()

        # add hooks and menu items
        # use wrap() instead of addHook to ensure menu already created 
        def ptkRebuildAddonsMenu(self):
            ptkMenu = None
            for menu in self._menus:
                if menu.title() == "Pinyin Toolkit":
                    ptkMenu = menu
                    break

            ptkMenu.addSeparator()
            config = getconfig()
            hooks.buildHooks(ptkMenu, mw, config, thenotifier, themediamanager,
                               updaters)

        aqt.addons.AddonManager.rebuildAddonsMenu = wrap(aqt.addons.AddonManager.rebuildAddonsMenu, ptkRebuildAddonsMenu) 
            
        # Tell Anki about the plugin
        # TODO: revisit this. upgrade to 2.0 call has changed to registerAddon but it doesn't do anything ...
        #mw.addonManager.registerAddon("Mandarin Chinese Pinyin Toolkit", 4)
        #self.registerStandardModels()
    
    def tryCreateAndLoadDatabase(self, mw, notifier):
        datatimestamp, satisfiers = pinyin.db.builder.getSatisfiers()
        cjklibtimestamp = os.path.getmtime(pinyin.utils.toolkitdir("pinyin", "vendor", "cjklib", "cjklib", "build", "builder.py"))
        
        if not(os.path.exists(dbpath)):
            # MUST rebuild - DB doesn't exist
            log.info("The database was missing entirely from %s. We had better build it!", dbpath)
            compulsory = True
        elif os.path.getmtime(dbpath) < cjklibtimestamp:
            # MUST rebuild - version upgrade might have changed DB format
            log.info("The cjklib was upgraded at %d, which is since the database was built (at %d) - for safety we must rebuild", cjklibtimestamp, os.path.getmtime(dbpath))
            compulsory = True
        elif os.path.getmtime(dbpath) < datatimestamp:
            # SHOULD rebuild
            log.info("The database had a timestamp of %d but we saw a data update at %d - let's rebuild", os.path.getmtime(dbpath), datatimestamp)
            compulsory = False
        else:
            # Do nothing
            log.info("Database up to date")
            compulsory = None
        
        if compulsory is not None:
            # We at least have the option to rebuild the DB: setup the builder
            dbbuilder = pinyin.db.builder.DBBuilder(satisfiers)
            
            # Show the form, which kicks off the builder and may give the user the option to cancel
            builddb = pinyin.forms.builddb.BuildDB(mw)
            # NB: VERY IMPORTANT to save the useless controller reference somewhere. This prevents the
            # QThread it spawns being garbage collected while the thread is still running! I hate PyQT4!
            _controller = pinyin.forms.builddbcontroller.BuildDBController(builddb, notifier, dbbuilder, compulsory)
            if builddb.exec_() == QDialog.Accepted:
                # Successful completion of the build process: replace the existing database, if any
                shutil.copyfile(dbbuilder.builtdatabasepath, dbpath)
            elif compulsory:
                # Eeek! The dialog was "rejected" despite being compulsory. This can only happen if there
                # was an error while building the database. Better give up now!
                return False
        
        # Finally, force the database connection to the (possibly fresh) DB to begin
        database()
        return True

    def registerStandardModels(self):
        # This code was added at the request of Damien: one of the changes in the next
        # Anki version will be to make language-specific toolkits into plugins.
        #
        # The code sets up a 'template' model for users. We probably want to customize
        # this eventually, but for now it's a duplicate of the old code from Anki.
        
        import anki.stdmodels
        from anki.models import Model, CardModel, FieldModel

        # Mandarin
        ##########################################################################

        def MandarinModel():
           m = Model(_("Mandarin"))
           f = FieldModel(u'Expression')
           f.quizFontSize = 72
           m.addFieldModel(f)
           m.addFieldModel(FieldModel(u'Meaning', False, False))
           m.addFieldModel(FieldModel(u'Reading', False, False))
           m.addCardModel(CardModel(u"Recognition",
                                    u"%(Expression)s",
                                    u"%(Reading)s<br>%(Meaning)s"))
           m.addCardModel(CardModel(u"Recall",
                                    u"%(Meaning)s",
                                    u"%(Expression)s<br>%(Reading)s",
                                    active=False))
           m.tags = u"Mandarin"
           return m

        anki.stdmodels.models['Mandarin'] = MandarinModel
