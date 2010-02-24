#!/usr/bin/env python
#-*- coding: utf-8 -*-

# You can get the list of fields you need to keep by examining
# the output of the database builder:
keepfields = ["kMandarin",   # Reading available for almost all characters, in frequency order
              "kXHC1983",    # Syllabised reading and unknown reference data from Xiàndài Hànyǔ Cídiǎn
              "kHanyuPinlu", # Reading and frequency data (relatively sparse) from Xiàndài Hànyǔ Pínlǜ Cídiǎn
              'kCompatibilityVariant',        #
              'kSemanticVariant',             #
              'kSimplifiedVariant',           # Variant data for traditional/simplified conversion
              'kSpecializedSemanticVariant',  #
              'kTraditionalVariant',          #
              'kZVariant'                     #
             ]

# Extract trimmed old data
unihan = open('Unihan.txt','r')
try:
    header = []
    outputdata = {}
    for line in unihan:
        if line.startswith("#") or len(line.strip()) == 0:
            header.append(line)
        else:
            character, field, data = line.split("\t")
            if field in keepfields:
                characterdata = outputdata.get(character, None)
                if characterdata is None:
                    characterdata = outputdata[character] = dict()
                
                characterdata[field] = data
finally:
    unihan.close()

# Overwrite with new data
unihan = open('Unihan.txt','w+')
try:
    unihan.writelines(header)
    # NB: doing things this way means that data for one character is all adjacent. This turns out to be important because
    # of how the cjklib Unihan reader is written (at least this was the case on 24/02/2010).
    for character, characterdata in outputdata.items():
        for field, fielddata in characterdata.items():
            unihan.write("%s\t%s\t%s" % (character, field, fielddata))
finally:
    unihan.close()
