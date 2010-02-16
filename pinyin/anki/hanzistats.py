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
from ankiqt import mw

import os
import codecs
import traceback
import sys

import pinyin.config
from pinyin.statisticsdata import *
from pinyin.logger import log
import pinyin.utils


#  SETTINGS
#  Give file address if you want additional characters to be considered as learned
#  e. g. FILE = os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt")
FILE = ""


####################################################################
#  Add Hanzi statisticts choice to the Tool menu.                  #
####################################################################
def init_hook():
    mw.mainWin.HanziStats = QtGui.QAction('Hanzi Statistics by PyTK', mw)
    mw.mainWin.HanziStats.setStatusTip('Hanzi Statistics by PyTK')
    mw.mainWin.HanziStats.setEnabled(True)
    mw.mainWin.HanziStats.setIcon(QtGui.QIcon("../icons/hanzi.png"))
    # the following line can be changed to customise your default view with the first zero after run representing simp/trad and the second seen/deck
    mw.connect(mw.mainWin.HanziStats, QtCore.SIGNAL('triggered()'), lambda: showMainPage(0, 0))
    mw.mainWin.menuTools.addAction(mw.mainWin.HanziStats)


####################################################################
#  Return all unique Hanzi in the current deck.                    #
####################################################################
def get_deckHanzi(DeckSeen):
    hanzi = set()
    
    # Bail out early if no deck is present yet
    if mw is None or mw.deck is None:
        return hanzi
    
    # Get Hanzi from the database
    # TODO: pass in the actual config object to determine the Expression field names
    hanzi_ids = mw.deck.s.column0("select id from fieldModels where name IN %s" % pinyin.utils.toSqlLiteral(pinyin.config.Config().candidateFieldNamesByKey['expression']))
    for hanzi_id in hanzi_ids:
        if DeckSeen == 0:
            hanzis = mw.deck.s.column0("select value from cards, fields where fieldModelID = :hid AND cards.factId = fields.factId AND cards.reps > 1", hid=hanzi_id)
        else:
            hanzis = mw.deck.s.column0("select value from fields where fieldModelID = :hid", hid=hanzi_id)
    
        hanzi.update(pinyin.utils.concat([[c for c in u if pinyin.utils.isHanzi(c)] for u in hanzis]))
    
    # Additionally get Hanzi from file
    if FILE:
        hanzi.update(get_fileHanzi(FILE))
    
    return hanzi

####################################################################
#  Return all unique Hanzi from file.                              #
####################################################################
def get_fileHanzi(file):
    try:
        f = codecs.open(file, "r", "utf8")
        return set(pinyin.utils.concat([[c for c in line if pinyin.utils.isHanzi(c)] for line in f.readlines()]))
    except IOError, e:
        log.exception("Error reading hanzi statistics character file " + file)
        return set()

####################################################################
#  Return all Hanzi we want to know about.                         #
####################################################################
def get_allHanzi(DeckSeen):
    hanzi = get_deckHanzi(DeckSeen)
    if FILE:
        hanzi.update(get_fileHanzi(FILE))
    return hanzi

####################################################################
#  Generic statistics computation                                  #
####################################################################
def classify(hanzi, groups):
    unclassifiedcount = 0
    groupcounts = [0 for _ in groups]
    for h in hanzi:
        for groupn, (group, grouphanzi) in enumerate(groups):
            if h in grouphanzi:
                groupcounts[groupn] += 1
                break
        else:
            unclassifiedcount += 1

    return groupcounts, unclassifiedcount

def get_genericstats(title, groups, unclassified_name, hanzi, backaction):
    groupcounts, unclassifiedcount = classify(hanzi, groups)

    # Create the HTML formatted output
    html = "<h4>%s</h4><table cellpadding=3><tr><td><b>Freq chars</b></td><td><b>Seen</b></td><td><b>Seen %%</b></td></tr>" % (title)
    python_actions = []

    makelinkhint = lambda base: filter(lambda x: x.isalnum(), "".join(list(set(base))))

    for (group, grouphanzi), groupcount in zip(groups, groupcounts):
        linkhint = makelinkhint(title + group)
        percentage = len(grouphanzi) != 0 and round(groupcount*100.0 / len(grouphanzi), 2) or 0.0
        html += u"<tr><td>%(group)s</td><td><a href=py:have%(hint)s>%(seen)s</a> of <a href=py:missing%(hint)s>%(total)s</a></a></td><td>%(percentage)s%%</td></tr>" \
                  % { "group" : group, "hint" : linkhint, "seen" : groupcount, "total" : len(grouphanzi), "percentage" : percentage }
        python_actions += [("have" + linkhint, lambda grouphanzi=grouphanzi: onShowHaveHanzi(grouphanzi, hanzi, backaction)),
                           ("missing" + linkhint, lambda grouphanzi=grouphanzi: onShowMissingHanzi(grouphanzi, hanzi, backaction))]

    if unclassified_name:
        linkhint = makelinkhint(title + unclassified_name)
        html += "<tr><td>%s</td><td><a href=py:other%s>%d</a></td><td></td></tr>" % (unclassified_name, linkhint, unclassifiedcount)
        python_actions += [("other" + linkhint, lambda: onShowOtherHanzi("".join([grouphanzi for _groupname, grouphanzi in groups]), hanzi, backaction))]

    return (html + "</table>", python_actions)

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the frequent  #
#  Hanzi lists.                                                    #
####################################################################
def get_freqstats(SimpTrad, hanzi, backaction):
    return get_genericstats("Character frequency data", [hanzi500sSimp, hanzi500sTrad][SimpTrad], "3500++", hanzi, backaction)

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the 4 HSK     #
#  Hanzi lists.                                                    #
####################################################################
def get_hskstats(hanzi, backaction):
    html, python_actions = get_genericstats("HSK character statistics", hanzihsk[:-1], None, hanzi, backaction)
    return (html + "<p><i>Note: This is not the same as HSK vocabulary.</i></p>", python_actions)

############################################################################
#  Return HTML formatted statistics on seen Hanzi in the 9 TW Grade Levels #
############################################################################
def get_twstats(hanzi, backaction):
    return get_genericstats("TW Ministry of Education List Statistics", hanzitaiwanstandard, None, hanzi, backaction)

###############################################
#  Choose an appropriate set of stats to show #
###############################################
def get_specificstats(SimpTrad, hanzi, backaction):
    if SimpTrad==0:
        return get_hskstats(hanzi, backaction)
    else:
        return get_twstats(hanzi, backaction)

####################################################################
#  Return HTML formatted statistics on seen Hanzi in the 4 TOP     #
#  Hanzi lists.                                                    #
####################################################################
# TODO: use this function
def get_topstats(hanzi, backaction):
    return get_genericstats("TOP Statistics (Characters)", hanzitop, None, hanzi, backaction)

####################################################################
#  "Main" function, run when Hanzi statistics is clicked in the    #
#  Tool menu.                                                      #
####################################################################
def showMainPage(SimpTrad, DeckSeen):
    # Set the prompt for seen cards vs whole deck toggle
    if DeckSeen == 0:
        seentype = "Data Set: <a href=py:toggleDeckSeen>seen cards only</a></small>"
    else:
        seentype = "Data Set: <a href=py:toggleDeckSeen>whole deck</a>"
    
    # Set the description for the traditional vs simplified toggle
    if SimpTrad == 0:
        ctype = "Character Set: <a href=py:toggleSimpTrad>Simplified</a>"
    else:
        ctype = "Character Set: <a href=py:toggleSimpTrad>Traditional</a>"

    hanzi = get_allHanzi(DeckSeen)
    
    backaction = lambda: showMainPage(SimpTrad, DeckSeen)
    freq_html, freq_python_actions = get_freqstats(SimpTrad, hanzi, backaction)
    specific_html, specific_python_actions = get_specificstats(SimpTrad, hanzi, backaction)
  
    html = "<h1>Hanzi Statistics</h1><h4>General</h4><br>" + ctype + "<br>" + seentype + \
           "<p>Unique Hanzi: <b><u>" + str(len(hanzi)) + "</></b></p>" + freq_html + "<br><br>" + specific_html
    python_actions = [("toggleDeckSeen", lambda: showMainPage(SimpTrad, not DeckSeen and 1 or 0)), ("toggleSimpTrad", lambda: showMainPage(not SimpTrad and 1 or 0, DeckSeen))]

    log.info("HTML: " + html)
    log.info("Actions: " + str(specific_python_actions))

    mw.help.showText(html, py=dict(python_actions + freq_python_actions + specific_python_actions))


####################################################################
#  Construct tables showing the missing and seen Hanzi.            #
####################################################################
def onShowMissingHanzi(grouphanzi, hanzi, backaction):
    log.info("Missing Hanzi link clicked!")
    return buildHanziPage("Missing Hanzi", [h for h in grouphanzi if h not in hanzi], backaction)

def onShowHaveHanzi(grouphanzi, hanzi, backaction):
    return buildHanziPage("Seen Hanzi", [h for h in grouphanzi if h in hanzi], backaction)

def onShowOtherHanzi(allgrouphanzi, hanzi, backaction):
    return buildHanziPage("Other Hanzi", [h for h in hanzi if h not in allgrouphanzi], backaction)

def buildHanziPage(title, hanzi, backaction):
    html = "<h1>" + title + "</h1>"
    html += "<a href=py:back>Go back</a><br><br>"
    html += '<font size=12 face="SimSun"><b>'
    for h in hanzi:
        html += '<a href="http://www.mdbg.net/chindict/chindict.php?page=worddictbasic&wdqb=' + h + '&wdrst=0&wdeac=1">' + h + '</a>'
    html += "</b></font>"
    
    mw.help.showText(html, py={"back": backaction})

if __name__ == "__main__":
  print "Don't run me.  I'm a plugin!"

else:
  mw.addHook('init', init_hook)
  log.info('HanziStats plugin loaded')

