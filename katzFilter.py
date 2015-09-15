import os
import sys
import re
import string
import nltk
from nltk import word_tokenize, pos_tag
import csv

JKFilterNounsList = ['nnnnnn','nnprnn','nninnn','jjnnnn','jjnn','cdnncd','cdnn','nncd','nnnn','nn','jj']        #nnx - NNP or NNS JJ CC PRP

def JKFilterForNoun(entity,flag):
    if flag == 0:
        POS_NOUN_PROPER = "NNP"
    else:
        POS_NOUN_PROPER = "NN"
    
    tokens = word_tokenize(entity)
    postag = nltk.pos_tag(tokens)
    posString=""
    
    for w1 in postag:
        if(w1[1].startswith(POS_NOUN_PROPER)):
            posString = posString + 'nn'
        elif(len(w1[1])>1 and w1[1]!='POS'):
            pt = w1[1].lower()
            posString = posString+ pt[:2]
    if(posString.replace('nn','')==''):		# if entity has only noun phrases
        retStr = ''
        for e in entity.split(' '):
            if len(e)>0 and e[0].isupper():
                retStr = retStr + ' ' + e
        retStr = retStr.strip()
        return True,retStr
## following for loop selects an entity part from the noun phrase
    for s in JKFilterNounsList:
        startIndex = posString.find(s)
        #print startIndex,s,posString
        if startIndex != -1:
            retString = ''
            si = (startIndex/2)		# 2 letters for one pos tag, like nn, cd,pr
            endi = ((len(s)/2)+(startIndex/2))           
            for k in range(si,endi,1):		# select only those words which have property defined in below if condition
                wordk = tokens[k]
                if wordk[0].isupper() or (postag[k][1] == 'PRP' and len(retString) != 0) or (postag[k][1] == 'IN' and len(retString) != 0) or postag[k][1] == 'CD' or postag[k][1].startswith(POS_NOUN_PROPER) or postag[k][1] == 'JJ':
                    retString = retString + ' ' + wordk    #
                # else:
                # 	break
            retString = retString.strip()    
            
            while(si > 0):
                if(postag[si-1][1].startswith(POS_NOUN_PROPER) or postag[si-1][1].startswith('CD')):
                    wordk = tokens[si-1]
                    if wordk[0].isupper() or postag[si-1][1].startswith('CD'):
                        retString = wordk +' '+ retString
                    si = si-1
                else:
                    break
            while(endi < len(tokens)):
                if(postag[endi][1].startswith(POS_NOUN_PROPER) or postag[endi][1].startswith('CD')):
                    wordk = tokens[endi]
                    if wordk[0].isupper() or postag[endi][1].startswith('CD'):
                        retString = retString + ' ' + wordk
                    endi +=1;
                else:
                    break    
            if(len(retString)>1):
                return True,retString
     
    return False,entity
    
def find(str, ch):
    for i, ltr in enumerate(str):
        if ltr == ch:
            yield i

##################
# input: noun phrase"
#  Input name is case sensitive. so Apoorv and apoorv will give different result. This is because Apoorv is a "NNP" in pos tagging and 
#  "apporv" is "NN".
##################
ent_name = raw_input("entity name: ")

flag,name = JKFilterForNoun(ent_name,0) #0 was used as a flag to choose on "NNP"(proper nouns). 
print flag,name    #if flag is False, that means no proper entity name is present in the text.


