#!/usr/bin/python
#-*- coding: utf-8 -*-

import time

from statisticsdata import *
import utils


hanziGrades = [grade for grade, _ in hanzihsk]

def hanziGrade(hanzi):
    if not utils.isHanzi(hanzi):
        return None
    
    for grade, hanzis in hanzihsk:
        if hanzi in hanzis:
            return grade
    
    # Default to Non-HSK
    return hanzihsk[-1][0]


# This function takes three arguments (firstAnsweredValues, daysInRange) where:
#  * 'firstAnsweredValues' is a list of (string, date, date) tuples where each string
#    value that has been answered occurs exactly once, and is paired with the date
#    at which it was first answered by the user and the date at which the card was created.
#  * 'daysInRange' is an integer expressing how many days of data should be returned.
#
# This function returns a tuple (days, cumulativeTotal, cumulativesByGrade) where:
#  * 'days' is a list of (negative) day indexes, with 0 representing today
#  * 'cumulativeTotal' is a list containing, for the corresponding day, the number
#    of hanzi that the user has "learned" up until the day
#  * 'cumulativesByGrade' is a dictionary of lists containing the same information, but
#    broken down by grade
def hanziDailyStats(firstAnsweredValues, daysInRange):
    # Holds, for each day, the set constructued by appending values of all fields
    # for the cards that were first answered on the given day and removing duplicates
    firstLearnedByDay = {}
    firstDay = 0
    endOfDay = time.time()
    for (value, firstAnswered, createdTime) in firstAnsweredValues:
        # To work around a former bug in Anki, if the answered date was 0 then use the card creation
        # date instead: <http://github.com/batterseapower/pinyin-toolkit/issues/closed/#issue/48>
        if firstAnswered == 0:
            firstAnswered = createdTime
        
        # FIXME: this doesn't account for midnightOffset
        day = int((firstAnswered - endOfDay) / 86400.0)
        firstLearnedByDay[day] = utils.updated(firstLearnedByDay.get(day, set()), set(value))
        
        # Record the earliest moment at which we answered any question
        if day < firstDay:
            firstDay = day

    # Internal state while we run time forward
    alreadyLearnt = set()
    cumulativeTotal = 0
    cumulativeByGrades = {}
    
    # Totals for output accumulated while running time forward
    days, cumulativeTotals, cumulativesByGrades = [], [], {}
    
    # The core of the algorithm. Run time forward:
    # NB: be careful to start at -daysInRange if we don't have data for
    # later times. This is to ensure we get an initial 0 when working out
    # what the graph x range should be later on, which is important to ensure
    # all the graph gets displayed on e.g. decks with large initial imports.
    # See <http://github.com/batterseapower/pinyin-toolkit/issues/#issue/69>
    for day in xrange(min(firstDay, -daysInRange), 1):
        for hanzi in firstLearnedByDay.get(day, set()):
            # First check: if we have already learnt this thing, we don't care
            if hanzi in alreadyLearnt:
                continue
            
            # Second check: if this thing is not actually a hanzi, we don't care
            grade = hanziGrade(hanzi)
            if grade is None:
                continue
            
            # It's new and it's a hanzi: remember we learnt it
            alreadyLearnt.add(hanzi)
            
            # Update running totals
            cumulativeTotal += 1
            cumulativeByGrades[grade] = cumulativeByGrades.get(grade, 0) + 1
        
        # We're done with the day. Add output to the graph if we are interested
        if day > -daysInRange:
            # X axis
            days.append(day)
            
            # "Total" Y axis
            cumulativeTotals.append(cumulativeTotal)
            
            # Other Y axes (one per grade)
            for grade in hanziGrades:
                cumulativesByGrades[grade] = cumulativeByGrade = cumulativesByGrades.get(grade, [])
                cumulativeByGrade.append(cumulativeByGrades.get(grade, 0))
    
    return days, cumulativeTotals, cumulativesByGrades
