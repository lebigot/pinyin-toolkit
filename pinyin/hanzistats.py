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
    # Get Hanzi from the database. This function has been carefully tuned to try and get good
    # performance, so be careful before you modify it! In particular:
    #  1) Doing *everything* in one huge query didn't work so well - perhaps sqlite's execution
    #     is not so good?
    #  2) It's essential to trim the amount of text you look at by only looking at fields with names
    #     like the ones we know about and suspect will contain Hanzi
    
    # Find all card models which come from Mandarin models
    cardmodels = session.all("select cardModels.id, cardModels.modelId, cardModels.qformat from cardModels, models where cardModels.modelId = models.id AND models.tags LIKE %s" % utils.toSqlLiteral("%" + config.modelTag + "%"))
    # Find the field names that are included in the *question field* of such cards
    cardmodelsfieldsnames = [(cmid, modelid, set([res["mappingkey"] for res in utils.parseFormatString(qformat) if isinstance(res, dict)])) for cmid, modelid, qformat in cardmodels]
    # Filter out unpromising names, and turn the remainder into the IDs of field models
    eligiblefields = set(utils.concat([config.candidateFieldNamesByKey[key] for key in ['expression', 'mw', 'trad', 'simp']]))
    cardmodelsfields = [(cmid, [session.scalar("select fieldModels.id from fieldModels where fieldModels.name = :name and fieldModels.modelId = :mid", name=fmname, mid=modelid) for fmname in fmnames if fmname in eligiblefields]) for cmid, modelid, fmnames in cardmodelsfieldsnames]
    
    # Look up the contents of fields whose Ids we found in the previous step, optionally only including
    # those whose corresponding card has been seen at least once
    hanziss = session.column0("SELECT fields.value FROM cards, fields WHERE cards.factId = fields.factId %s AND (%s)" % \
                              ((DeckSeen == 0) and "AND cards.reps > 0" or "", # Only look for seen cards if we are in that mode
                               " OR ".join(["(cards.cardModelId = %s AND fields.fieldModelID IN %s)" % (utils.toSqlLiteral(cmid), utils.toSqlLiteral(fmids)) for cmid, fmids in cardmodelsfields])))
    
    # Flatten everything into a set with *no intermediate structures*
    allhanzis = set()
    for hanzis in hanziss:
        allhanzis.update([c for c in hanzis if utils.isHanzi(c)])
    
    return allhanzis

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
    html = "<h4>%s</h4><table cellpadding=3><tr><td><b>Category</b></td><td><b>Seen</b></td><td><b>Seen %%</b></td></tr>" % (title)
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
    html, python_actions = get_genericstats("HSK Hanzi", hanzihsk[:-1], None, hanzi, backaction)
    return (html + "<p><i>Note: This is not the same as HSK <b>vocabulary</b>.</i></p>", python_actions)

def get_twstats(hanzi, backaction):
    return get_genericstats("Taiwan Education Ministry Hanzi", hanzitaiwanstandard, None, hanzi, backaction)

def get_topstats(hanzi, backaction):
    return get_genericstats("Test Of Proficiency (TOP) Hanzi", hanzitop, None, hanzi, backaction)

####################################################################
#  "Main" function, run when Hanzi statistics is clicked in the    #
#  Tool menu.                                                      #
####################################################################
def hanziStats(config, session):
    def go(SimpTrad, DeckSeen):
        # Setup toggles for view options
        deckseen_html = "Data Set: <a href=py:toggleDeckSeen>%s</a>" % (DeckSeen == 0 and "seen cards only" or "all cards")
        simptrad_html = "Character Set: <a href=py:toggleSimpTrad>%s</a>" % (SimpTrad == 0 and "Simplified" or "Traditional")
        toggle_html = deckseen_html + "<br>" + simptrad_html
        toggle_python_actions = [("toggleDeckSeen", lambda: go(SimpTrad, not DeckSeen and 1 or 0)), ("toggleSimpTrad", lambda: go(not SimpTrad and 1 or 0, DeckSeen))]

        hanzi = filter(lambda c: characterIsSimpTrad(c, SimpTrad), get_allHanzi(config, session, DeckSeen))

        def backaction():
            freq_html, freq_python_actions = get_freqstats(SimpTrad, hanzi, backaction)
        
            if SimpTrad == 0:
                specific_html, specific_python_actions = get_hskstats(hanzi, backaction)
            else:
                tw_html, tw_python_actions = get_twstats(hanzi, backaction)
                top_html, top_python_actions = get_topstats(hanzi, backaction)
                specific_html, specific_python_actions = tw_html + "<br>" + top_html, tw_python_actions + top_python_actions

            html = "<h1>Hanzi Statistics</h1>" + toggle_html + \
                   "<h4>General</h4>" + \
                   "<p>Unique Hanzi: <b><u>" + str(len(hanzi)) + "</u></b></p>" + \
                   "<p>" + freq_html + "</p><br>" + \
                   "<p>" + specific_html + "</p>"
        
            return html, (toggle_python_actions + freq_python_actions + specific_python_actions)

        return backaction()
  
    return go(config.prefersimptrad == "trad" and 1 or 0, 0)


def characterIsSimpTrad(c, simpTrad):
    from db import database
    from cjklib import characterlookup
    
    thislocale, otherlocale = simpTrad == 0 and ("C", "T") or ("T", "C")
    clookup = characterlookup.CharacterLookup(thislocale, dbConnectInst=database()) # NB: not sure that thisLocale actualy makes any difference..

    # Find all the variants of this character for the relevant locales
    othervariants = clookup.getCharacterVariants(c, otherlocale)
    thisvariants = clookup.getCharacterVariants(c, thislocale)
    
    # If there are any variants at all, guess that we must have a character in the original locale.
    # To deal nicely with situations where we lack data, guess that things are in the requested locale
    # if we *also* don't have any versions of them in the original locale.
    return len(othervariants) != 0 or len(thisvariants) == 0
