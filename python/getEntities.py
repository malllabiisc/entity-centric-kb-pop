import os
import string
import sys
import re
import mongodbClass as mdb
import nltk
from nltk import word_tokenize, pos_tag
# create/use a database and collection.
dbObj = None

def find(str, ch):
    for i, ltr in enumerate(str):
        if ltr == ch:
            yield i

def getRelationAndEntity(line):
    splChars = ['-','_','[',']']
    for sc in splChars:
        line = line.replace(sc, ' ')
    line = ' '.join(line.split(' '))
    start = line.find(':');                         #ollie output format = confidence: (ent1;rel;ent2)
    if start > 0:
     prob = line[0:start]                           #capture the confidence of the extraction
     extractionStart = line.find('(');              #start of ent1 after '('
     entities =  list(find(line,';'));              #ent and rel are separated by ';' so get all those indexes.
     if extractionStart > 0 and len(entities)>1:
         ent1 = line[extractionStart+1:entities[0]];    #get ent1 which is between ( and ;
         rel1 = line[entities[0]+1:entities[1]];        #get rel which is between ; and ;
         ent2 = line[entities[1]+1:];        #get ent2 which is between ; and end of line-1
         #ent2 = ent2.strip(')')
         return prob+"_"+ent1+"_"+rel1+"_"+ent2;
    return None;

def collectEntities(primaryEnt,url):
    print "inside getent"
    global dbObj
    dbObj = mdb.mongodbDatabase('triples_collection')

    allExt = mdb.mongodbDatabase('all_ext_collection')
    allExtCol = allExt.docCollection
    extObj = allExtCol.find_one({'primaryEnt':primaryEnt,'url':url})
    if extObj == None:
        print "No extractions", primaryEnt
        return None

    data = extObj.get('extList')
    ent1List = [];
    ent2List = [];
    relList = [];
    probList = []

    for line in data:
      line = line.encode('utf-8','ignore')
      if len(line) > 1:                                 #if the line has some string
        result = getRelationAndEntity(line);
        if(result != None):
            ereList = result.split("_")
            if(len(ereList[2].split(' ')) < 7 and len(ereList[3].split(' ')) < 8):
                e2 = ereList[3].strip()
                r = ereList[2].strip()
                try:
                    words1 = word_tokenize(e2);
                    postag1 = nltk.pos_tag(words1)
                    if(len(postag1)>0):
                        w1 = postag1[0]
                        if(w1[1] == "IN" or w1[1] == "PREP" or w1[1] == "TO"):
                            tmp = e2.split(' ')
                            e2 = ' '.join(tmp[1:])
                            r = r + " " + str(tmp[0])
                            ent1List.append(ereList[1]);                         #store ent1, rel and ent2
                            ent2List.append(e2);
                            relList.append(r);
                            probList.append(ereList[0])
                            #print ereList[1], " --> ", r
                        else:
                            probList.append(ereList[0]);
                            ent1List.append(ereList[1]);                         #store ent1, rel and ent2
                            ent2List.append(ereList[3]);
                            relList.append(ereList[2]);
                except Exception,e:
                    print "error ",e


    finalTripleSet = set()
    for i in range(len(ent1List)):
        prob = probList[i]
        pent = ent1List[i];
        strent = ent2List[i];
        strrel = relList[i];

        pent = pent.replace(")","").replace("-"," ")
        pent = pent.replace("(","")
        numbers = re.findall(r'\[([^]]*)\]',strent)
        if(len(numbers) !=0):
            for num in numbers:
                strent = string.replace(strent,"["+num+"]","")

        numbers = re.findall(r'\[([^]]*)\]',strrel)
        if(len(numbers) !=0):
            for num in numbers:
                strrel = string.replace(strrel,"["+num+"]","")

        numbers = re.findall(r'\[([^]]*)\]',pent)
        if(len(numbers) !=0):
            for num in numbers:
                pent = string.replace(pent,"["+num+"]","")
        if(not('[attrib=' in strent)):
            strent = strent.strip('.')
            strent = strent.strip(',')
            strent = strent.strip()

            pent = pent.strip('.')
            pent = pent.strip(',')
            pent = pent.strip()

            strent = strent.replace("\"", "").replace("-"," ")
            strent = string.replace(strent, ")", "")
            strent = string.replace(strent,"(","")
            strent = string.replace(strent,"\'","")
            strrel = strrel.strip()
            strrel = string.replace(strrel,",","")
            strrel = string.replace(strrel,"\'","")
            strrel = string.replace(strrel,")","")

            triple_i = pent + " : " + strrel + " : " + strent + ":" + prob;
            finalTripleSet.add(triple_i)

    tripleList = []
    for i in finalTripleSet:
        tripleList.append(i)

    # store the extracted triple list in the database as processed data
    # primary entity will be the key and triples are stored as document
    col = dbObj.docCollection
    oldVal = col.find_one({'primaryEnt':primaryEnt,'url':url})

    if oldVal == None:
        newVal = {'primaryEnt':primaryEnt, 'url':url,'output_set':tripleList}
        print "inserted into triples list ", primaryEnt, "len", len(tripleList)
        col.insert_one(newVal)
    else:
        # convert oldlist to set. remove duplicates
        oldList = oldVal.get('output_set')

        for o in oldList:
            finalTripleSet.add(o)
        tripleList = []
        for t in finalTripleSet:
            tripleList.append(t)

        newVal =  {'primaryEnt':primaryEnt, 'url': url, 'output_set':tripleList}
        col.replace_one({'primaryEnt':primaryEnt, 'url':url},newVal,True)
        print "updated the triple list", primaryEnt, "len", len(tripleList)
    allExt.client.close()
    dbObj.client.close()

#collectEntities("Bangalore")
