# -*- coding: utf-8 -*-

import unittest

from pinyin.dictionaryonline import *


class ParseGoogleResponseTest(unittest.TestCase):
    def testParseNumber(self):
        self.assertEquals(parsegoogleresponse('1'), 1L)
    
    def testParseNegativeNumber(self):
        self.assertEquals(parsegoogleresponse('-1'), -1L)
    
    def testParseString(self):
        self.assertEquals(parsegoogleresponse('"hello"'), "hello")
    
    def testParseCheck(self):
        rspChunk = '[[["Good","好","","Hǎo"]],[["adjective",["good"],[["good",["好","良好","优良","善","佳","良"]]]],["adverb",["well","OK","fine","okay","okey","okey dokey"],[["well",["很好","好","顺利","舒服","安好","顺"]],["OK",["好"]],["fine",["好","非常好"]],["okay",["好"]],["okey",["好"]],["okey dokey",["好"]]]],["interjection",["OK","okay","okey"],[["OK",["行","好","对"]],["okay",["好","行","对"]],["okey",["好","对","行"]]]],["verb",["love","like"],[["love",["爱","喜欢","喜爱","恋爱","恋","好"]],["like",["喜欢","喜爱","爱","喜","喜好","好"]]]]],"zh-CN",,[["Good",[5],0,0,1000,0,1,0]],[["好",4,,,""],["好",5,[["Good",1000,0,0],["a good",0,0,0],["well",0,0,0],["is good",0,0,0],["OK",0,0,0]],[[0,1]],"好"]],,,[["zh-CN"]],46]';
        self.assertEquals(parsegoogleresponse(rspChunk), "")
    
    def testParseStringWithEscapes(self):
        self.assertEquals(parsegoogleresponse('"hello\\t\\"world\\""'), 'hello\t"world"')
        self.assertEquals(parsegoogleresponse('"\\tleading whitespace"'), '\tleading whitespace')
    
    def testParseUnicodeString(self):
        self.assertEquals(parsegoogleresponse(u'"好"'), u'好')
    
    def testParseList(self):
        self.assertEquals(parsegoogleresponse('[1, "hello", 10, "world", 1337]'), [1, "hello", 10, "world", 1337])
    
    def testParseListOfLists(self):
        self.assertEquals(parsegoogleresponse('[1, [2, [3, 4]], [5, 6]]'), [1, [2, [3, 4]], [5, 6]])
    
    def testParseDict(self):
        self.assertEquals(parsegoogleresponse('{"fruit" : "orange", 1 : 2, "buy" : 1337}'), {"fruit" : "orange", 1 : 2, "buy" : 1337})
    
    def testParseDictOfDicts(self):
        self.assertEquals(parsegoogleresponse('{"fruits" : {"orange" : 1, "banana" : 2}, "numbers" : {1337 : ["cool"], 13 : ["bad", "unlucky"]}}'),
                                              {"fruits" : {"orange" : 1, "banana" : 2}, "numbers" : {1337 : ["cool"], 13 : ["bad", "unlucky"]}})
    
    def testParseWhitespace(self):
        self.assertEquals(parsegoogleresponse('[ 1    ,"hello",[10, "barr rr"],   "world"   , 1337, {     "a" :   "dict"} ]'), [1, "hello", [10, "barr rr"], "world", 1337, { "a": "dict" }])
    
    def testParseErrorIfTrailingStuff(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('1 1'))
        self.assertRaises(ValueError, lambda: parsegoogleresponse('"hello" 1'))
        self.assertRaises(ValueError, lambda: parsegoogleresponse('[1] 1'))
    
    def testParseErrorIfUnknownCharacters(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('! "hello" !'))
    
    def testParseErrorIfListNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('[ "hello"'))
    
    def testParseErrorIfDictMissingValueNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" }'))
        self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" : }'))
    
    def testParseErrorIfDictNotClosed(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse('{ "hello" : "world"'))
    
    def testParseErrorIfEmpty(self):
        self.assertRaises(ValueError, lambda: parsegoogleresponse(''))

class GoogleTranslateTest(unittest.TestCase):
    def testTranslateNothing(self):
        self.assertEquals(gTrans(""), None)
    
    def testTranslateEnglish(self):
        self.assertEquals(gTrans(u"你好，你是我的朋友吗？"), [[Word(Text(u'Hello, you are my friend?'))]])
    
    def testTranslateFrench(self):
        self.assertEquals(gTrans(u"你好，你是我的朋友吗？", "fr"), [[Word(Text(u'Bonjour, vous \xeates mon ami?'))]])
    
    def testTranslateIdentity(self):
        self.assertEquals(gTrans(u"canttranslatemefromchinese"), None)
    
    def testTranslateStripsHtml(self):
        self.assertEquals(gTrans(u"你好，你<b>是我的</b>朋友吗？"), [[Word(Text(u'Hello, you are my friend?'))]])

    # Annoyingly, this fails. This means that simplified/traditional translation doesn't preserve whitespace:
    # def testTranslatePreservesWhitespace(self):
    #     self.assertEquals(gTrans(u"\t个个个\t个个\t", "zh-tw"), [[Word(Text(u'\t个个个\t个个\t'))]])
    
    def testTranslateDealsWithDefinition(self):
        self.assertEquals(gTrans(u"好"), [
            [Word(Text("Well"))],
            [Word(Text("Verb: like, love"))],
            [Word(Text("Adjective: good"))],
            [Word(Text("Adverb: fine, OK, okay, okey, okey dokey, well"))],
            [Word(Text("Interjection: OK!, okay!, okey!"))]
          ])
    
    def testCheck(self):
        self.assertEquals(gCheck(), True)

if __name__ == '__main__':
    unittest.main()

