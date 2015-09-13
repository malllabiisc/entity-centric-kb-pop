import os
import mongodbClass as mdb
import multiprocessing
from multiprocessing import Process, Queue
from os import getpid
import csv
import re

allset = set()
finalList = []
def searchWord(rel,relPhrase):
    relWords = rel.split(' ')
    phraseWords = relPhrase.split(' ')
    for rw in relWords:
        if rw not in phraseWords:
            #print rw, " not present in ", relPhrase
            return False
    return True

def getRelation(relPhrase,type1, type2):
    dbObj = mdb.mongodbDatabase('nell_collection')
    col = dbObj.docCollection

    typeDbObj = mdb.mongodbDatabase('ontology_collection')
    typeCol = typeDbObj.docCollection

    words = relPhrase.split(' ')
    min = 1000000   #some big number. I am too optimistic here by selecting a such a big number
    reqWord = None
    finalNellRelations = set()
    # to get the word which has less number of relations
    # in relation "want to"
    for w in words:
        val = col.find_one({'word':w})
        if val != None:
            relList = val.get('list')
            if len(relList) < min:
                reqWord = w
                min = len(relList)
    nellRelDict = {}
    if reqWord != None:
        #print "req word for ", relPhrase , " is ", reqWord 
        # get list of phrases containing 'reqword' 
        val = col.find_one({'word':reqWord})
        if val != None:
            relList = val.get('list')
            for rel in relList:
                isPresent = searchWord(relPhrase, rel[0])
                if isPresent:
                    finalNellRelations.add(rel[1])
                    #print "nell relation for ", relPhrase, " is ", rel[1]
                    d = typeCol.find_one({'rel':rel[1].lower()}) #get type of the nell relation
                    if d != None:
                        nellType1 = d.get('domain')
                        nellType2 = d.get('range')
##                        if relPhrase == "moved to":
##                            print nellType1, " ", nellType2, " ", rel[1]," ",relPhrase
                        if type1 == None:
                            type1 = []
                        if type2 == None:
                            type2 = []
                        if (nellType1 in type1) and (nellType2 in type2):
                            freq = nellRelDict.get(rel[1])
                            if freq == None:
                                freq = 1
                            else:
                                freq = freq + 1
                            nellRelDict.update({rel[1]:freq})
                            

    return finalNellRelations, nellRelDict
            
def getType(ent):
    dbObj = mdb.mongodbDatabase('ent_type_collection')
    col = dbObj.docCollection
    val = col.find_one({'ent':ent})
    if val != None:
        return val.get('type')
    else:
        suffix = ent;
        t = None
        while(t==None):
            try:
                words = suffix.split(' ')
                suffix = ' '.join(words[1:])
                t=col.find_one({'ent':suffix})
                if t != None:
                    dbObj.client.close()
                    return t.get('type')
            except:
                dbObj.client.close()
                return None
    dbObj.client.close()
    return None

def getTypeHierarchy(enttype):
    dbObj = mdb.mongodbDatabase('type_hierarchy_collection')
    col = dbObj.docCollection
    allTypeList = []
    for ent in enttype:
        allTypeList.append(ent)
        
        val = col.find_one({'ent':ent})
        if val != None:
            tl = val.get('typelist')
            for t in tl:
                if t not in allTypeList:
                    allTypeList.append(t)
    return allTypeList

def mapEtractionsToNell(line, entSearch):
    dbObj = mdb.mongodbDatabase('ent_type_collection')
    col = dbObj.docCollection
    nellExt = mdb.mongodbDatabase('map_collection')
    mapcol = nellExt.docCollection

    outputEntityList = []
    ent1 = line[0].strip()
    ent2 = line[2].strip()
    rel = line[1].strip()
    
    ent1type = getType(ent1.lower())
    ent2type = getType(ent2.lower())
    # print ent1, ent1type
    # print ent2, ent2type
    ent1type_hier = getTypeHierarchy(ent1type)
    ent2type_hier = getTypeHierarchy(ent2type)
    
    nellRelSet, freqDict = getRelation(rel, ent1type_hier, ent2type_hier)
    setDictList = [nellRelSet,freqDict]
    
    entType = 0
    relType = 0
    if ent1.lower() in entSearch or entSearch in ent1.lower():
        val = col.find_one({'ent':ent2.lower()})
        if val != None:
            entType = 1
        else:
            entType = 2
    else:
        val = col.find_one({'ent':ent1.lower()})
        if val != None:
            entType = 1
        else:
            entType = 2
    
##    print line
##    print ent1.lower(), "-->", ent1type_hier
##    print ent2.lower(), "-->", ent2type_hier
    if len(nellRelSet) == 0:
        relType = 2
    else:
        relType = 1
    
    newFact = 1
    isnew = mapcol.find({'ent1':ent1})
    if isnew != None:
        for facts in isnew:
            nelRel = facts.get('rel')
            nelEnt2 = facts.get('ent2')
            if nelRel == rel and nelEnt2==ent2:
                newFact = 0
    fact = ent1 + " " + rel
    outputEntityList.append(ent1)
    outputEntityList.append(rel)

##    for nr in nellRelSet:
##        #print rel, " --type-- ", nr
##        outputEntityList.append(nr)
    
    mx = 0
    nellRel = ''
    for nr in freqDict.keys():
        count = freqDict.get(nr)
        if count > mx:
            mx = count
            nellRel = nr
    if nellRel != '':
        outputEntityList.append(nellRel)
##    
    outputEntityList.append(ent2)
    fact += " "+ent2
    if relType == 1 and entType == 1:
        extType = 1
    elif relType == 1 and entType == 2:
        extType = 2
    elif relType == 2 and entType == 1:
        extType = 3
    elif relType == 2 and entType == 2:
        extType = 4
    
    outputEntityList.append(extType)
##    if newFact == 1:
##        outputEntityList.append('new')
    return outputEntityList
    
def getNellRelations(data,entSearch):
    global allset
    global finalList

    relPhraseDict = {}
    processList = []
    #data = open('outputEnt.csv','r').readlines()
    input = []
    q = Queue()
    entFileName = "_".join(entSearch.split(' '))
    #if not os.path.exists('extractions/'+domain+'/'+ entFileName +'.csv'):
    multiProcControll = 0
    for l in data:
        ot = mapEtractionsToNell(l,entSearch)
        finalList.append(ot)

def inference_test(entSearch):
    global finalList
    dbObj = mdb.mongodbDatabase('final_triples')
    col = dbObj.docCollection
    entList = []
    vals = col.find_one({'primaryEnt':entSearch})
    if vals == None:
        print "No extractions"
        count = 0
    else:
        data = vals.get('final-triples')
        if len(data) > 0 :
            getNellRelations(data,entSearch)
            outputFileName = entSearch.replace(' ','_') +'.csv'
            fw = open(outputFileName, 'w')
            fileWriter = csv.writer(fw)
            fileWriter.writerows(finalList)
            finalList = []
            fw.close()
    dbObj.client.close()

def getsetready(cat):
    global allset
    data = open('extractions/'+cat+'_result.csv','r').readlines()
    for d in data:
        l = d.split(',')
        rs = l[1].strip()
        r = ' '.join(rs.split())
        allset.add(r)
