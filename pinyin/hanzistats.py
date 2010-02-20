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

from statisticsdata import *
from logger import log
import utils


#  SETTINGS
#  Give file address if you want additional characters to be considered as learned
#  e. g. FILE = os.path.join(mw.config.configPath, "plugins", "known_hanzi.txt")
FILE = ""


####################################################################
#  Return all unique Hanzi in the current deck.                    #
####################################################################
def get_deckHanzi(config, session, DeckSeen):
    hanzi = set()
    
    # Get Hanzi from the database
    # TODO: pass in the actual config object to determine the Expression field names
    hanzi_ids = session.column0("select id from fieldModels where name IN %s" % utils.toSqlLiteral(config.candidateFieldNamesByKey['expression']))
    for hanzi_id in hanzi_ids:
        if DeckSeen == 0:
            hanzis = session.column0("select value from cards, fields where fieldModelID = :hid AND cards.factId = fields.factId AND cards.reps > 0", hid=hanzi_id)
        else:
            hanzis = session.column0("select value from fields where fieldModelID = :hid", hid=hanzi_id)
    
        hanzi.update(utils.concat([[c for c in u if utils.isHanzi(c)] for u in hanzis]))
    
    return hanzi

####################################################################
#  Return all unique Hanzi from file.                              #
####################################################################
def get_fileHanzi(file):
    try:
        f = codecs.open(file, "r", "utf8")
        return set(utils.concat([[c for c in line if utils.isHanzi(c)] for line in f.readlines()]))
    except IOError, e:
        log.exception("Error reading hanzi statistics character file " + file)
        return set()

####################################################################
#  Return all Hanzi we want to know about.                         #
####################################################################
def get_allHanzi(config, session, DeckSeen):
    hanzi = get_deckHanzi(config, session, DeckSeen)
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
        python_actions += [("have" + linkhint, lambda grouphanzi=grouphanzi: showHaveHanzi(grouphanzi, hanzi, backaction)),
                           ("missing" + linkhint, lambda grouphanzi=grouphanzi: showMissingHanzi(grouphanzi, hanzi, backaction))]

    if unclassified_name:
        linkhint = makelinkhint(title + unclassified_name)
        html += "<tr><td>%s</td><td><a href=py:other%s>%d</a></td><td></td></tr>" % (unclassified_name, linkhint, unclassifiedcount)
        python_actions += [("other" + linkhint, lambda: showOtherHanzi("".join([grouphanzi for _groupname, grouphanzi in groups]), hanzi, backaction))]

    return (html + "</table>", python_actions)

####################################################################
#  Construct tables showing the missing and seen Hanzi.            #
####################################################################
def showMissingHanzi(grouphanzi, hanzi, backaction):
    return showHanziPage("Missing Hanzi", [h for h in grouphanzi if h not in hanzi], backaction)

def showHaveHanzi(grouphanzi, hanzi, backaction):
    return showHanziPage("Seen Hanzi", [h for h in grouphanzi if h in hanzi], backaction)

def showOtherHanzi(allgrouphanzi, hanzi, backaction):
    return showHanziPage("Other Hanzi", [h for h in hanzi if h not in allgrouphanzi], backaction)

def showHanziPage(title, hanzi, backaction):
    html = "<h1>" + title + "</h1>"
    html += "<a href=py:back>Go back</a><br><br>"
    html += '<font size=12 face="SimSun"><b>'
    for h in hanzi:
        html += '<a href="http://www.mdbg.net/chindict/chindict.php?page=worddictbasic&wdqb=' + h + '&wdrst=0&wdeac=1">' + h + '</a>'
    html += "</b></font>"

    return html, [("back", backaction)]

###############################################
#  Possible statistics we are interested in   #
###############################################
def get_freqstats(SimpTrad, hanzi, backaction):
    return get_genericstats("Character frequency data", [hanzi500sSimp, hanzi500sTrad][SimpTrad], "3500++", hanzi, backaction)

def get_hskstats(hanzi, backaction):
    html, python_actions = get_genericstats("HSK character statistics", hanzihsk[:-1], None, hanzi, backaction)
    return (html + "<p><i>Note: This is not the same as HSK vocabulary.</i></p>", python_actions)

def get_twstats(hanzi, backaction):
    return get_genericstats("TW Ministry of Education List Statistics", hanzitaiwanstandard, None, hanzi, backaction)

# TODO: use this function
def get_topstats(hanzi, backaction):
    return get_genericstats("TOP Statistics (Characters)", hanzitop, None, hanzi, backaction)


####################################################################
#  "Main" function, run when Hanzi statistics is clicked in the    #
#  Tool menu.                                                      #
####################################################################
def hanziStats(config, session):
    def go(SimpTrad, DeckSeen):
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

        hanzi = get_allHanzi(config, session, DeckSeen)

        backaction = lambda: go(SimpTrad, DeckSeen)
        freq_html, freq_python_actions = get_freqstats(SimpTrad, hanzi, backaction)
        specific_html, specific_python_actions = SimpTrad == 0 and get_hskstats(hanzi, backaction) or get_twstats(hanzi, backaction)

        html = "<h1>Hanzi Statistics</h1><h4>General</h4><br>" + ctype + "<br>" + seentype + \
               "<p>Unique Hanzi: <b><u>" + str(len(hanzi)) + "</u></b></p>" + \
               freq_html + "<br><br>" + \
               specific_html
        python_actions = [("toggleDeckSeen", lambda: go(SimpTrad, not DeckSeen and 1 or 0)), ("toggleSimpTrad", lambda: go(not SimpTrad and 1 or 0, DeckSeen))]

        return html, (python_actions + freq_python_actions + specific_python_actions)
  
    return go(config.prefersimptrad == "trad" and 1 or 0, 0)
