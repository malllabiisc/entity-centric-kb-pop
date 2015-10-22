import os
import sys
import re
import string
import gensim, logging
from gensim.models import word2vec
import nltk
from nltk import word_tokenize, pos_tag
import numpy
import solr
import csv
import mongodbClass as mdb
#from parMapNell import getNellRelations
from getNameFromPhrase import getEntityName
from pymongo import MongoClient

newRelation = {}
nearEntityMapInCanopy = {}
entity1ToFreebaseId = {}
entity2ToFreebaseId = {}
wordCountDict={}
wordToCanopyNo = {}
canopySetDict = {}
entityToCanopyMap = {}
clusterSetInCanopy = {}
newEntityList = []
goalEntity = []
ent1List = [];
ent2List = [];
relList = [];
probList = [];
numpyMatrix = numpy.zeros((10,10))
urlIdList = []
#model = word2vec.Word2Vec.load_word2vec_format('../EntityCentricKB/GoogleNews-vectors-negative300.bin',binary=True)
#model = gensim.models.Word2Vec.load('/tmp/symModel')
model = word2vec.Word2Vec.load_word2vec_format('vectors.bin',binary=True)
threshold = 0.1;
entSearch = ""


JKFilterNounsList = ['nnprnn','nninnn','jjnnnn','jjnn','cdnncd','cdnn','nncd','nnnn','nn','jj']        #nnx - NNP or NNS JJ CC PRP

# create/use a database and collection.
dbObj = None



class nodeStructure():
    def __init__(self,node,prob):
        self.similarityValue = prob;    # similarity between two entities
        self.nodeId = node;             # this field to hold the entity id.

def printTheGraph():
  ln = len(nearEntityMapInCanopy);
  keyList = nearEntityMapInCanopy.keys();
  orig_stdout = sys.stdout
  fname  = '_'.join(entSearch.split()) + "group.txt"
  p = file('extractions/ercm/'+fname,'w')
  sys.stdout = p
  for i in keyList:
    ndlist = nearEntityMapInCanopy.get(i)
    for ndset in ndlist:
        if(len(ndset)>=1):
            for entno in ndset:
                mid = entity2ToFreebaseId.get(entno)
                freebaseId = "--"
                if(mid != None):
                    freebaseId = str(mid)
                newString = ent1List[entno] + " : " + relList[entno] + " : " + ent2List[entno]
                print newString
            print "---------------------------"
  sys.stdout = orig_stdout
  p.close()

def JKFilterForNoun(entity,flag):
    if flag == 0:
        POS_NOUN_PROPER = "NNP"
    else:
        POS_NOUN_PROPER = "NN"
    tokens = word_tokenize(entity)
    postag = nltk.pos_tag(tokens)
    posString=""
    if entity == entSearch:
        return True,entity
    for w1 in postag:
        if(w1[1].startswith("NN")):
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
        if startIndex != -1:
            retString = ''
            si = (startIndex/2)		# 2 letters for one pos tag, like nn, cd,pr
            endi = ((len(s)/2)+(startIndex/2))           
            for k in range(si,endi,1):		# select only those words which have property defined in below if condition
                wordk = tokens[k]
                if wordk[0].isupper() or (postag[k][1] == 'PRP' and len(retString) != 0) or (postag[k][1] == 'IN' and len(retString) != 0) or postag[k][1] == 'CD' or postag[k][1].startswith(POS_NOUN_PROPER) or postag[k][1] == 'JJ' or searchPrimaryEntity(wordk):
                    retString = retString + ' ' + wordk    #
            retString = retString.strip()    
            
            while(si > 0):
                if(postag[si-1][1].startswith('NN') or postag[si-1][1].startswith('CD')):
                    wordk = tokens[si-1]
                    if wordk[0].isupper() or postag[si-1][1].startswith('CD'):
                        retString = wordk +' '+ retString
                    si = si-1
                else:
                    break
            while(endi < len(tokens)):
                if(postag[endi][1].startswith('NN') or postag[endi][1].startswith('CD')):
                    wordk = tokens[endi]
                    if wordk[0].isupper() or postag[endi][1].startswith('CD'):
                        retString = retString + ' ' + wordk
                    endi +=1;
                else:
                    break    
            if(len(retString)>1):
                return True,retString
    for ge in goalEntity:
        if not (ge in entity):
            return False,''
    return True,entSearch

def SelectEntity(entSet):
    scoreDict = {}
    for ent in entSet:
        for line in ent1List[ent]:
            for l in goalEntity:
                if(l in line.lower() and checkValidNoun(l, "NNP")):
                    scoreDict.update({ent:5})
        mid = entity2ToFreebaseId.get(ent)
        if(mid!=None):
            score = scoreDict.get(ent)
            if(score != None):
                scoreDict.update({ent:(score+1)})

        score = scoreDict.get(ent)
        if(score == None):
            score = 0
            
        relword = word_tokenize(relList[ent])
        score += min(3,len(relword))
        words1 = word_tokenize(ent1List[ent])
        postag1 = nltk.pos_tag(words1)
        
        for w1 in postag1:
            if((w1[1].startswith("NN") or w1[1] == "JJ")):
                score = score + 1
                break
        
        words1 = word_tokenize(ent2List[ent])
        postag1 = nltk.pos_tag(words1)
        
        for w1 in postag1:
            if((w1[1].startswith("NN") or w1[1] == "JJ")):
                score = score + 1
                break
        scoreDict.update({ent:score})
    max1 = -1
    entNumber = 0
    for ent in scoreDict:
        score = scoreDict.get(ent)
        if(score > max1):
            entNumber = ent
            max1 = score
    return entNumber
    
def checkValidNoun(oldStr,POS_NOUN_PROPER):
    words = word_tokenize(oldStr)
    postag = nltk.pos_tag(words)
    validNoun = False
    for w1 in postag:
        if(w1[1].startswith(POS_NOUN_PROPER) or w1[1]== "CD" or w1[0][0].isupper() or w1[1]== "JJ" ):
            validNoun = True
    return validNoun

def searchPrimaryEntity(line):
    line = ' '.join(line.split(' '))
    for l in goalEntity:
        if(l in line.lower()):
            #print " line ", line, "has ",l
            return True
    return False

def someRandomFunction(entNumber,outputLine,key):
    mid1 = entity1ToFreebaseId.get(entNumber)
    mid2 = entity2ToFreebaseId.get(entNumber)
    if mid1 == None:
        mid1 = ''
    if mid2 == None:
        mid2 = ''
    
    ent_flag = oneOrTwo(ent1List[entNumber])
    fb1,filterEnt1 = getEntityName(ent1List[entNumber])
    fb2,filterEnt2 = getEntityName(ent2List[entNumber])
    
    filterEnt1 = filterEnt1.strip()
    filterEnt2 = filterEnt2.strip()
    if (filterEnt1.lower()).count(entSearch.lower()) > 1:
        filterEnt1 = entSearch
    if (filterEnt2.lower()).count(entSearch.lower()) > 1:
        filterEnt2 = entSearch
    
    isPrimaryEnt1 = searchPrimaryEntity(filterEnt1)
    isPrimaryEnt2 = searchPrimaryEntity(filterEnt2)
    curOutputList = []
    if(fb1 and fb2 and len(filterEnt1)>0 and len(filterEnt2)>0 and (isPrimaryEnt1 or isPrimaryEnt2)):
        if not (filterEnt1 + " " + relList[entNumber] + " " + filterEnt2 in outputLine):
            curOutputList = [filterEnt1,relList[entNumber],filterEnt2,probList[entNumber],urlIdList[entNumber],key] # key is used as cluster id
            outputLine.add(filterEnt1 + " " + relList[entNumber] + " " + filterEnt2)
    return curOutputList,outputLine

def posNewRelations():
    cluster_obj = mdb.mongodbDatabase('cluster_info')
    cluster_col = cluster_obj.docCollection

    fe_db = mdb.mongodbDatabase('final_triples')
    final_col = fe_db.docCollection
    
    flag=0
    entNumber = 0
    keyList = nearEntityMapInCanopy.keys();
    outputEntityList = []
    outputLine = set()
    for i in keyList:
        ndlist = nearEntityMapInCanopy.get(i)
        for ndset in ndlist:
            # print "ndlist size",len(ndlist)
            if(len(ndset)==1):
                entNumber = ndset.pop()
                ndset.add(entNumber)
                curOutputList,outputLine = someRandomFunction(entNumber,outputLine,i)
                if curOutputList != None and len(curOutputList) != 0:
                    outputEntityList.append(curOutputList)
                    clusterone = cluster_col.find_one({'primaryEnt':entSearch,'url':urlIdList[entNumber],'key':i})
                    tmpdoc = {'primaryEnt':entSearch,'url':urlIdList[entNumber],'similar_facts':[curOutputList],'key':i}
                    if clusterone == None:
                        cluster_col.insert_one(tmpdoc)
                    else:
                        cluster_col.replace_one({'primaryEnt':entSearch,'url':urlIdList[entNumber],'key':i},tmpdoc,True)
            #outputEntityList.append([newEnt1,mid1,relList[entNumber],newEnt2,mid2,isPrimaryEnt])
            else:
                clusterList = clusterRelation(ndset)
                for subSets in clusterList:
                    if(len(subSets)>=1):
                        entNumber = SelectEntity(subSets)
                        curOutputList,outputLine = someRandomFunction(entNumber,outputLine,i)
                        if curOutputList != None and len(curOutputList) != 0:
                            outputEntityList.append(curOutputList)
                            allOutputList = []
                            # print "len of set",len(subSets)
                            for eno in subSets:
                                allOutputList.append([ent1List[eno],relList[eno],ent2List[eno],probList[eno],urlIdList[eno]])

                            clusterone = cluster_col.find_one({'primaryEnt':entSearch,'url':urlIdList[entNumber],'key':i})
                            if clusterone == None:
                                cluster_col.insert_one({'primaryEnt':entSearch,'url':urlIdList[entNumber],'similar_facts':allOutputList,'key':i})
                            else:
                                cluster_col.replace_one({'primaryEnt':entSearch,'url':urlIdList[entNumber],'key':i},{'primaryEnt':entSearch,'url':urlIdList[entNumber],'similar_facts':allOutputList,'key':i},True)
    #fw = open('extractions/'+ entSearch+'/data/output/'+entSearch+'outputEnt.csv', 'w')
    #fileWriter = csv.writer(fw)
    #fileWriter.writerows(outputEntityList)
    #fw.close()
    oldVal = final_col.find_one({'primaryEnt':entSearch})
    if oldVal == None:
        final_col.insert_one({'primaryEnt':entSearch,'final-triples':outputEntityList})
    else:
        d = {'primaryEnt':entSearch,'final-triples':outputEntityList}
        final_col.replace_one({'primaryEnt':entSearch},d,True)
    cluster_obj.client.close()
    fe_db.client.close()
    #getNellRelations(outputLine)
    
def find(strs, ch):
    for i, ltr in enumerate(strs):
        if ltr == ch:
            yield i

def wordCount(wordList):
    for str in wordList:
        if str!='':
            if(wordCountDict.has_key(str)):
                count = wordCountDict.get(str)
                count+=1
                wordCountDict.update({str:count})            
            else:
                wordCountDict.update({str:1})

def findSimilarity(ent1,ent2,canopyId,ent1id,ent2id):
    confScore = 0;
    ent1 = ent1.strip();
    ent2 = ent2.strip();
    wordList1 = word_tokenize(ent1)#ent1.split(" ");
    wordList2 = word_tokenize(ent2)#ent2.split(" ");
    words1 = word_tokenize(ent1);
    postag1 = nltk.pos_tag(words1)
    words2 = word_tokenize(ent2);
    postag2 = nltk.pos_tag(words2);
    
    mid1 = entity2ToFreebaseId.get(ent1id)
    mid2 = entity2ToFreebaseId.get(ent2id)
    
    if(mid1 != None and mid2 != None):
        if(mid1==mid2):
            return 1;
        else:
            return 0;
        
    for w1 in postag1:
        if(not(w1[1].startswith("NN") or w1[1] == "CD" or w1[1] == "JJ")):
            try:
                wordList1.remove(w1[0]);
            except:
                pass

    for w2 in postag2:
        if(not(w2[1].startswith("NN") or w2[1] == "CD" or w2[1] == "JJ")):
            try:
                wordList2.remove(w2[0]);
            except:
                pass
    if(canopyId!=None):
        try:
            wordList1.remove(canopyId);
            wordList2.remove(canopyId);
        except:
            return 0;
    
    if(len(wordList1)==0 and len(wordList2)==0):
        return 1;
    
    if(len(wordList1)==0):
        sim = 0;
        for w in wordList2:
            try:
                sim = sim + model.similarity(w,canopyId);
            except:
                sim = 0;
        sim = sim / len(wordList2);
        return sim;
    
    elif(len(wordList2)==0):
        sim = 0;
        for w in wordList1:
            try:
                sim = sim + model.similarity(w,canopyId);
            except:
                sim = 0;
        sim = sim / len(wordList1);
        return sim;
    else:
        for w1 in wordList1:
            # c1 = wordCountDict.get(w1);
            # if(c1 == None):
            c1=1;
            cs = set()
            for w2 in wordList2:
                if(len(w1)>0 and len(w2)>0):
                    if (w1==w2):
                        sim = 1
                    else:
                        try:
                            sim = model.similarity(w1,w2);
                        except:
                            sim = 0;
                    cs.add(sim)
            cs.add(0);
            c1=1;
            confScore = confScore + (max(cs) / (float(c1)));
        if(len(wordList1) >= 1):
            confScore = confScore / (len(wordList1))
        return confScore;

def entitySetSimilarity(set1,set2):
    simFactor = 0;
    if(len(set1)==0 or len(set2)==0):
        return 0;
    if(set1!=None):
            set1_ToList = []
            for ent in set1:
                set1_ToList.append(ent)
    if(set2 != None):
            set2_ToList = []
            for ent in set2:
                set2_ToList.append(ent)
    similarityScore = 0         #find similarity between each entity in one canopy
    ConfScore = 0;
    count = 0;
    for p in set1_ToList:
        for q in set2_ToList:
            if(q != p):
                processp = oneOrTwo(ent2List[p])
                if processp:
                    A = ent1List[p]
                else:
                    A = ent2List[p]
                processq = oneOrTwo(ent2List[q])
                if processq:
                    B = ent1List[q]
                else:
                    B = ent2List[q]
                similarityScore += findSimilarity(A,B,None,p,q)  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                count += 1
            else:
                similarityScore +=1;
                count +=1;
    if(count > 0):
        confScore = similarityScore/(count)
    else:
        confScore = 0
    return confScore
    
    
def constructCanopy(entity,entNo,cnpNo):        #set of entities inside dictionary.
    words = word_tokenize(entity)
    postag = nltk.pos_tag(words)
    canopyset = set()
    try:
        for w in postag:
            entSet = set();
            if((w[0] != '[' and w[0]!=']') and (w[1].startswith("NN") or w[1] == "CD" or w[1] == "JJ")):
                if(wordToCanopyNo.get(w[0])==None):
                    entSet.add(entNo);
                    wordToCanopyNo.update({w[0]:cnpNo})             # canopy for each word. store count:word in dictionary
                    canopySetDict.update({w[0]:entSet})            # canopyNumber:entSet in dictionary
                    #canopyset.add(cnpNo);
                    canopyset.add(w[0]);
                    entityToCanopyMap.update({entNo:canopyset})
                    cnpNo = cnpNo+1;
                else:
                    c = wordToCanopyNo.get(w[0])
                    canopyset.add(w[0])                             # entity to canopy map
                    entSet = canopySetDict.get(w[0]);
                    entSet.add(entNo);
                    canopySetDict.update({w[0]:entSet});
                    entityToCanopyMap.update({entNo:canopyset})        # entiy to canopy Map, entityNumber:Set of Canopy
    except:
        return cnpNo
    return cnpNo

def clusterInCanopy():              #clustering inside canopy
    print "ent 1 list size ", len(ent1List)
    print "ent 2 list size ", len(ent2List)
    failure = 0;
    length = len(canopySetDict)
    keys = canopySetDict.keys();    #word to set of entities dictionary
    maxConfScore = threshold
    for k in keys:
        nearEntityMap = {}
        setval = canopySetDict.get(k);  #get the set of enties inside the canopy 'k'
        if(setval!=None):
            setToList = []
            for ent in setval:
                setToList.append(ent)   #convert ent set to list
            ln = len(setToList);
            if(ln >=1):
                for j in setToList:         #find similarity between each entity in one canopy
                    #wordsInEnt1 = ent2List[j].split(' ')
                    nodeList = [];
                    nearEnt = j;
                    maxConfScore = threshold;
                    for x in setToList:
                        if(x != j):
                            #wordsInEnt2 = ent2List[x].split(' ')    #get the next entity in the cluster to find the similarity
                            #similarityScore = findSimilarity(wordsInEnt1,wordsInEnt2,k);  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                            processj = oneOrTwo(ent2List[j])
                            if processj:
                                A = ent1List[j]
                            else:
                                A = ent2List[j]
                            processx = oneOrTwo(ent2List[x])
                            if processx:
                                B = ent1List[x]
                            else:
                                B = ent2List[x]

                            similarityScore = findSimilarity(A,B,k,j,x);  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                            
                            if(similarityScore > maxConfScore):
                                maxConfScore = similarityScore;         
                                nearEnt = x;                            #find the closest entity
                    nearEntityMap.update({j:nearEnt})
                simKey = nearEntityMap.keys();
                clusterList = [];               #List of Set entities to hold the cluster in one canopy.
                for sk in simKey:
                    clusterSet = set()
                    nEnt = nearEntityMap.get(sk)
                    if(nEnt == sk):
                        clusterSet.add(sk);
                        del nearEntityMap[sk];
                        #simKey.remove(sk)
                    else:
                        clusterSet.add(sk)
                        if( nearEntityMap.get(nEnt) == sk):         # if a is closest to b and b is closest to a put them in a set
                            clusterSet.add(nEnt)
                            del nearEntityMap[nEnt]
                            simKey.remove(nEnt)
                        del nearEntityMap[sk]
                        #simKey.remove(sk)
                    clusterList.append(clusterSet)
                    
                del nearEntityMap;
                flag = 1;
                while(flag==1):
                    clLen = len(clusterList);
                    flag=0;
                    for i in range(0,len(clusterList),1):#print str(i)+"no inc y"
                        nearEnt = i;
                        set1 = clusterList[i];
                        maxScore = threshold;
                        for j in range(i+1,len(clusterList),1):
                            set2 = clusterList[j];
                            mergeScore = SetSimilarity(set1,set2,k);
                            if(mergeScore > maxScore):
                                maxScore = mergeScore;
                                nearEnt = j;
                        if(nearEnt != i):
                            flag=1;
                            maxScore = threshold;
                            nearSet = clusterList[nearEnt]
                            set1 = set1.union(nearSet);
                            clusterList[i] = set1;
                            clusterList[nearEnt] = set()
            nearEntityMapInCanopy.update({k:clusterList})

def SetSimilarity(set1,set2,k):
    simFactor = 0;
    if(len(set1)==0 or len(set2)==0):
        return 0;
    if(set1!=None):
            set1_ToList = []
            for ent in set1:
                set1_ToList.append(ent)
    if(set2 != None):
            set2_ToList = []
            for ent in set2:
                set2_ToList.append(ent)
    similarityScore = 0         #find similarity between each entity in one canopy
    ConfScore = 0;
    count = 0;
    for p in set1_ToList:
        for q in set2_ToList:
            if(q != p):
                processp = oneOrTwo(ent2List[p])
                if processp:
                    A = ent1List[p]
                else:
                    A = ent2List[p]
                processq = oneOrTwo(ent2List[q])
                if processq:
                    B = ent1List[q]
                else:
                    B = ent2List[q]

                similarityScore += findSimilarity(A,B,k,p,q)  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                count += 1
            else:
                similarityScore +=1;
                count +=1;
    if(count > 0):
        confScore = similarityScore/(count)
    else:
        confScore = 0
    return confScore
    
def MergeClusters():        #Merging of clusters which are in different canopy.
    keySet = nearEntityMapInCanopy.keys();
    for k in keySet:
        cList = nearEntityMapInCanopy.get(k);  # List of set
        #print "canopy and ent " + k + str(cList)
        length = len(cList);
        for p in range(0,length,1):
            set1 = cList[p]
            for ent in set1:
                otherCnpSet = entityToCanopyMap.get(ent)        # get the list of canopies which have same entity
                for s in otherCnpSet:
                    if(s!=k):
                        #print s + "not equal to" + k;
                        otherList = nearEntityMapInCanopy.get(s);
                        for othersets in otherList:
                            cfactor = len(othersets.intersection(set1))
                            if(cfactor>=1):          #this is not a strict factor. can improve the logic here
                                #print "sim set" + s+ "-->" + str(othersets) + k +"-->"+ str (set1)
                                set1 = set1.union(othersets);
                                cList[p] = set1;
                                otherList.remove(othersets)
        nearEntityMapInCanopy.update({k:cList})
                    

def clusterRelation(setval):              #clustering inside canopy
    maxConfScore = threshold
    setToList = []
    clusterList = [];                     #List of Set entities to hold the cluster in one canopy.
    nearEntityMap = {}
    for ent in setval:
        setToList.append(ent)   #convert ent set to list
    ln = len(setToList);
    if(ln >=1):
        for j in setToList:         #find similarity between each entity in one canopy
            #wordsInEnt1 = ent2List[j].split(' ')
            nodeList = [];
            nearEnt = j;
            maxConfScore = threshold;
            for x in setToList:
                if(x != j):
                    #wordsInEnt2 = ent2List[x].split(' ')    #get the next entity in the cluster to find the similarity
                    #similarityScore = findSimilarity(wordsInEnt1,wordsInEnt2,k);  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                    similarityScore = findSimilarity(relList[j],relList[x],None,j,x);  # wordsInEnt1,wordsInEnt2 are from ent2, but from different line
                    if(similarityScore > maxConfScore):
                        maxConfScore = similarityScore;         
                        nearEnt = x;                            #find the closest entity
            nearEntityMap.update({j:nearEnt})
        simKey = nearEntityMap.keys();
        for sk in simKey:
            clusterSet = set()
            nEnt = nearEntityMap.get(sk)
            if(nEnt == sk):
                clusterSet.add(sk);
                del nearEntityMap[sk];
                #simKey.remove(sk)
            else:
                clusterSet.add(sk)
                if( nearEntityMap.get(nEnt) == sk):         # if a is closest to b and b is closest to a put them in a set
                    clusterSet.add(nEnt)
                    del nearEntityMap[nEnt]
                    simKey.remove(nEnt)
                del nearEntityMap[sk]
                #simKey.remove(sk)
            clusterList.append(clusterSet)
            
        del nearEntityMap;
        flag = 1;
        while(flag==1):
            clLen = len(clusterList);
            flag=0;
            for i in range(0,len(clusterList),1):#print str(i)+"no inc y"
                nearEnt = i;
                set1 = clusterList[i];
                maxScore = threshold;
                for j in range(i+1,len(clusterList),1):
                    set2 = clusterList[j];
                    mergeScore = SetSimilarity(set1,set2,None);
                    if(mergeScore > maxScore):
                        maxScore = mergeScore;
                        nearEnt = j;       #get a nearest set
                if(nearEnt != i):       #if there exists a nearest set
                    flag=1;
                    maxScore = threshold;
                    nearSet = clusterList[nearEnt]
                    set1 = set1.union(nearSet);         #join 2 nearest sets
                    clusterList[i] = set1;      
                    clusterList[nearEnt] = set()
    return clusterList

def searchClueweb(entityList,entityToFreebaseId):
    #connection
    conn = solr.SolrConnection('http://localhost:8983/solr')
    # do a search
    for k in range (len(entityList)):
        ent = entityList[k]
        ent = ent.strip(' ')
        words = word_tokenize(ent)
        postag = nltk.pos_tag(words)
        searchString = ""
        for w in postag:
            if(w[1].startswith("NN") or (w[1].startswith("PRP")) or w[1] == "JJ"):
                word = w[0]
                searchString = searchString + str(word) + " "
        searchString = searchString.strip(" ")	
        searchString = searchString.replace(" ","\ ")
        q  = 'id:'+searchString
        try:
            response = conn.query(q);
            if(len(response.results)>=1):
                for hit in response.results:
                    entityToFreebaseId.update({k:hit['author']})
                    print "success in cn",k
        except:
            print "fail in cn",k
    return entityToFreebaseId

def oneOrTwo(entList):
    wordsInEnt = entList.split(' ')
    process = False;
    for line in wordsInEnt:
        for ge in goalEntity:
            if(ge in line.lower() or (line.lower().find(ge))!= -1):
                process = True
    return process

def InitialSetup():
    global dbObj
    global ent1List
    global ent2List
    global relList
    global probList
    global urlIdList
    noOfCanopyEntries = 0;
    
    # filename = entSearch+"list.txt"
    # data = open(filename).readlines()
    listofSet=[];
    col = dbObj.docCollection
    oldValues = col.find({'primaryEnt':entSearch})

    print "triples extracted from ", entSearch
    if oldValues == None:
        print "No extractions", entSearch
        return None

    
    for oldVal in oldValues:
        data = oldVal.get('output_set')

        uniurl = oldVal.get('url')
        url = uniurl.encode('utf-8','ignore')
        print "len of data ",len(data), "url ",url
        for uniline in data:
            try:
                line = uniline.encode('utf-8','ignore')
                process = False;
                for l in goalEntity:
                    if(l in line.lower() or (line.lower().find(l))!= -1):
                        process = True;
                if(process):
                    entities =  list(find(line,':'));
                    if(len(entities)>=2):              #ent and rel are separated by ':' so get all those indexes.
                        ent1 = line[0:entities[0]]
                        # print "test 0"
                        numbers = re.findall(r'\[([^]]*)\]',ent1)
                        # print "test 1"
                        if(len(numbers) !=0):
                            for num in numbers:
                                ent1 = ent1.replace("["+num+"]","")
                        ent1 = ent1.replace(" LRB ", "").replace(" RRB ", "").replace(",", "")
                        ent1List.append(ent1)
                        relList.append(line[entities[0]+1:entities[1]]) 

                        ent2 = line[entities[1]+1:entities[2]]
                        ent2 = ent2.replace(" LRB ", "").replace(" RRB ", "").replace(",", "")
                        ent2List.append(ent2)
                        probList.append(line[entities[2]+1:len(line)])
                        urlIdList.append(url)
            except Exception,e:
                print "error in init ", e
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
   
    #print "ent line score"+ str(len(ent1List))
    # print "test 3.0"
    for k in range(0,len(ent2List),1):
        # wordsInEnt2 = ent2List[k].split(' ')
        # wordCount(wordsInEnt2)
        process = oneOrTwo(ent2List[k])
        if(process):
            noOfCanopyEntries = constructCanopy(ent1List[k],k,noOfCanopyEntries)
        else:
            noOfCanopyEntries = constructCanopy(ent2List[k],k,noOfCanopyEntries)

def entityClusterAndNormalise(ent):
    global entSearch
    global goalEntity	
    global entity1ToFreebaseId
    global entity2ToFreebaseId
    global ent1List
    global ent2List
    global relList
    global newRelation
    global nearEntityMapInCanopy
    global wordCountDict
    global wordToCanopyNo
    global canopySetDict
    global entityToCanopyMap
    global clusterSetInCanopy
    global newEntityList
    global dbObj
    
    dbObj =  mdb.mongodbDatabase('triples_collection')
    ent1List = []
    ent2List = []
    relList = []
    newRelation = {}
    nearEntityMapInCanopy = {}
    entity1ToFreebaseId = {}
    entity2ToFreebaseId = {}
    wordCountDict={}
    wordToCanopyNo = {}
    canopySetDict = {}
    entityToCanopyMap = {}
    clusterSetInCanopy = {}
    newEntityList = []
    goalEntity = []

    entSearch  = ent
    words = word_tokenize(entSearch)
    postag = pos_tag(words)
    for w1 in postag:
        if((w1[1].startswith("NN") or w1[1] == "JJ" or w1[1]=="CD") and len(w1[0]) > 1):
            goalEntity.append(w1[0].lower())
    if len(goalEntity)==0:
        print "no key word in goal entity",entSearch
        return
    InitialSetup();
    # entity1ToFreebaseId =  searchClueweb(ent1List,entity1ToFreebaseId);
    # entity2ToFreebaseId =  searchClueweb(ent2List,entity2ToFreebaseId);
    clusterInCanopy()
    MergeClusters()
    posNewRelations()
    dbObj.client.close()
    

#entityClusterAndNormalise('Galileo Galilei')
