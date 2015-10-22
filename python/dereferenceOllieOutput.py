import os
import json
from xml.dom import minidom
import sys
import re
import string
from nltk import word_tokenize,pos_tag
from dependencyParsing import getDependencyList
from nounDependency import getNounDependency
import mongodbClass as mdb
import xml
from getEntities import collectEntities

primaryEnt = ''

# create/use a database and collection.
dbObj = None
allExt = None

ollieFilesDict = {}
corefFilesDict = {}
extractionList = []     # per sentence extraction details
sentenceList = []
pronounToReplaceList = ['he','i','my','me','she','him','her','it','they','their','them','himself','herself','this',
                        'that','those','these','whom','whose','who','we']
pronounDict = {}
replaceList = []

def xmlParseCorefResult(xmlStr):
    #xmldoc = minidom.parse(filename) #enter the xml filename here
    try:
        xmldoc = xml.dom.minidom.parseString(xmlStr)
        coreftag = xmldoc.getElementsByTagName('coreference')[0] #returns a list of things withing tag
        # print coreftag
        coref = coreftag.getElementsByTagName('coreference')
    except Exception,e:
        print "parse error ****",e
        coref = []
    # print coref
    corefdata = []
    try:
        for ref in coref:
            mention = ref.getElementsByTagName('mention')
            listofelemsforref = []
            m_counter = 0
            for m in mention:
                templist = []
                elementlist = []
                sentence = m.getElementsByTagName('sentence')
                start = m.getElementsByTagName('start')
                end = m.getElementsByTagName('end')
                # print end.firstChild.data
                head = m.getElementsByTagName('head')
                # print head.firstChild.data
                text = m.getElementsByTagName('text')

                # print text.firstChild.data
                sen = int(sentence[0].firstChild.data)
                begin = int(start[0].firstChild.data)
                terminate = int(end[0].firstChild.data)
                headword = int(head[0].firstChild.data)
                data = (text[0].firstChild.data).encode('utf-8','ignore')
                templist = [data,sen-1,headword-1,begin-1,terminate-1]
                if m_counter == 0:
                    headworddata = templist[:]
                else: 
                    elementlist = templist[:]
                    pywrapperform = [elementlist,headworddata]
                    # print pywrapperform
                    listofelemsforref.append(pywrapperform)
                    # print m_counter
                    # raw_input('Press enter')
                m_counter += 1
            corefdata.append(listofelemsforref)
    except:
        print "xml error "
        corefdata = []
    return corefdata

def createPronounDict():
	global pronounDict
	for index, word in enumerate(pronounToReplaceList):
		pronounDict.update({word:index})

def find(str, ch):
    for i, ltr in enumerate(str):
        if ltr == ch:
            yield i

def getRelationAndEntity(line):
    start = line.find(':');                         #ollie output format = confidence: (ent1;rel;ent2)
    if start > 0:
        prob = line[0:start]                           #capture the confidence of the extraction
        extractionStart = line.find('(');              #start of ent1 after '('
        entities =  list(find(line,';'));              #ent and rel are separated by ';' so get all those indexes.
        ereList = []            
        if extractionStart > 0 and len(entities)>1:
            ent1 = line[extractionStart+1:entities[0]];    #get ent1 which is between ( and ;
            rel1 = line[entities[0]+1:entities[1]];        #get rel which is between ; and ;
            ent2 = line[entities[1]+1:len(line)-1];        #get ent2 which is between ; and end of line-1
            ent2 = ent2.strip(')')
            ereList.append(ent1)
            ereList.append(rel1)
            ereList.append(ent2)
            return prob,ereList
    return None,None;

    
def storeInDb(sentenceToExtractionMap,sentencewiseCorefResultDict,url):
    global allExt
    allExt = mdb.mongodbDatabase('all_ext_collection')
    allExtCol = allExt.docCollection
    
    extObj = allExtCol.find_one({'primaryEnt':primaryEnt,'url':url})
    if extObj == None:
        finalList = []
    else:
        finalList = extObj.get('extList')
    keySet = sentenceToExtractionMap.keys()
    for elemnt in keySet:
        extlist = sentenceToExtractionMap.get(elemnt)
        for e in range(0,len(extlist),1):
            if len(extlist[e]) > 0 and extlist[e] != '\n':
                extractionLine = extlist[e].strip('\n')
                finalList.append(extractionLine)
    if extObj == None:
        allExtCol.insert_one({'primaryEnt':primaryEnt, 'url':url, 'extList':finalList})
    else:
        d = {'primaryEnt':primaryEnt, 'url':url, 'extList':finalList}
        allExtCol.replace_one({'primaryEnt':primaryEnt, 'url':url},d,True)
    allExt.client.close()

def multiplePronoun(coreflist):
    multipleProNounList = []
    listlen = len(coreflist)
    for i in range(listlen-1):
        npl1 = coreflist[i]
        noun1 = npl1[0]
        pro1 = npl1[1]
        for j in range(i+1,listlen,1):
            multiplePNList = []
            npl2 = coreflist[j]
            noun2 = npl2[0]
            pro2 = npl2[1]
            if pro1 == pro2 and noun1 != noun2:
                multiplePNList.append(pro1)
                multiplePNList.append(noun1)
                multiplePNList.append(noun2)
                multiplePNList.append(npl1[2])  #start index
                multiplePNList.append(npl2[2])
                multiplePNList.append(npl1[3])  #end index
                multiplePNList.append(npl2[3])
                multipleProNounList.append(multiplePNList)
                #coreflist.remove(npl1)
                coreflist[i]=[]
                #listlen = listlen - 1
    return multipleProNounList,coreflist

def pronounMatching(entity,ent_no,pro,noun):
    for index,word in enumerate(word_tokenize(entity)):
        if(word.lower() == pro.lower() and (pronounDict.get(pro.lower())!=None)):        #simple case: replace the pronoun which is there in list and sentence.
            return (True,ent_no,index)                             # e.g: he: lives in : bangalore--> replace he by noun
        elif(word.lower() == pro.lower() and (pro in noun)):                    # case2: e.g: Obama : be president of : America
            tokens = word_tokenize(noun)                    # pro here is "Obama" noun may be "President, Barack Obama"       
            postag = pos_tag(tokens)
            for w in postag:
                if(not(w[1].startswith("NN") or w[1]=="JJ") and len(w[0])>1):
                    return (False,0,0)                            #It will not replace if noun has pos tag other than adjectives and NNP/NNS
            return (True,ent_no,index)
    return None,None,None

def ReplacingRules(entRelList,noun,pro):
    global pronounDict
    pronounDict = {}
    try:
        createPronounDict()
        line = ""
        line = ' '.join(entRelList)
        if pro.lower()==noun.lower():
            return (False,0,0)
    ##    if(len(word_tokenize(noun))>5):
    ##        return (False,0,0)
        if (noun.lower() in line.lower().strip()) and (noun.lower() not in pro.lower()):
            return (False,0,0)
        
        noun_replace = True
        tokens = word_tokenize(noun)
        postag = pos_tag(tokens)
        for w in postag:
            if(not(w[1].startswith("NN") or w[1]=="JJ") and len(w[0])>1):
                noun_replace = False
        if len(word_tokenize(pro)) == 1:
            bool,eno,index = pronounMatching(entRelList[0],0,pro,noun)
            if(bool!=None):
                return bool,eno,index
            
            bool,eno,index = pronounMatching(entRelList[2],2,pro,noun)
            if(bool!=None):
                return bool,eno,index
        elif(pro in entRelList[0] and noun_replace):     # if pronoun is a list of words, then find the count of substrings
            noOfPro = 0
            if(entRelList[0].find(pro)==0 and len(entRelList[0])==len(pro)):
                noOfPro =  entRelList[0].count(pro)
            elif(entRelList[0].find(pro)==0):
                noOfPro =  entRelList[0].count(pro+' ')
            elif(entRelList[0].find(pro)== len(entRelList[0])-len(pro)):
                noOfPro =  entRelList[0].count(' '+pro)
            else:
                noOfPro =  entRelList[0].count(' '+pro+' ')
            if(noOfPro==1):
                return (True,0,-1)                                          # if only one appearance, then replace it by whole,no need to tokenize.
        elif(pro in entRelList[2] and noun_replace):     
            noOfPro = 0
            if(entRelList[2].find(pro)==0 and len(entRelList[2])==len(pro)):
                noOfPro =  entRelList[2].count(pro)
            elif(entRelList[2].find(pro)==0):
                noOfPro =  entRelList[2].count(pro+' ')
            elif(entRelList[2].find(pro)== len(entRelList[2])-len(pro)):
                noOfPro =  entRelList[2].count(' '+pro)
            else:
                noOfPro =  entRelList[2].count(' '+pro+' ')
            if(noOfPro==1):
                return (True,2,-1)    
    except:
        return (False,0,0)

    return (False,0,0)

def getCount(str1,str2):
    count = 0
    for s1 in str1.split(' '):
        for s2 in str2.split(' '):
            if s1==s2:
                count+=1
                break
    return count

def getProperNoun(pronoun,noun1,noun2,erelist,sentNo,filedata,pindex1,pindex2):
    objList = getDependencyList(filedata,sentNo)
    try:         
        proObj1 = objList[pindex1+1]
        proObj2 = objList[pindex2+1]
        
        line = ""
        line = ' '.join(erelist)
        if proObj1.name == pronoun and proObj2.name == pronoun:
            matchLine1 = ""
            matchLine2 = ""
            depList = []
            #print "list values " + str(proObj1.depObjList)
            if len(proObj1.depObjList) != 0:
                depList = proObj1.depObjList.sort()
            depList.append(proObj1.parent)
            depList = depList.sort()
            if depList != None:
                for s in depList:
                    matchLine1 = matchLine1 + objList[s].name
            depList = []
            if len(proObj1.depObjList) != 0:
                depList = proObj2.depObjList.sort()
            depList.append(proObj2.parent)
            depList = depList.sort()
            if depList != None:
                for s in depList:
                    matchLine2 = matchLine2 + objList[s].name    
            count1 = getCount(matchLine1,line)
            count2 = getCount(matchLine2,line)
            if count1 >= count2:
                return noun1
            else:
                return noun2
    except:
        return noun1
    
def ReplaceCorefPointers(primaryEntity,url):
    global primaryEnt
    global extractionList
    global replaceList
    global dbObj
    replaceList = []
    print "deref for ",primaryEntity
    primaryEnt = primaryEntity
    primaryEntDict = {}
    setForReplacement = set()
    
    filewiseInfoDict = {}

    primaryEntSet = set()
    primaryEntSet.add(primaryEntity)
    
    ollieOutput = "openieOutputFolder"
    corefOutput = "corefOutputFolder"
    
    dbObj = mdb.mongodbDatabase('tmp_collection')
    tempCol = dbObj.docCollection
    tmp = tempCol.find_one({'primaryEnt':primaryEntity, 'url':url})
    key = url
    
    ollieDataList = tmp['openie']
    corenlpData = tmp['corenlp']
    key = url
    #initialise dictionaries
    sentenceToExtractionMap = {} 
    sentencewiseCorefResultDict = {}
    #initialise lists
    extractionList = []
            
    perSentenceData = []        # holds sentence + all extractions of a sentence from ollie output
    
    for ollie in ollieDataList:
        ollie = ollie.encode('utf-8','ignore')
        lines = ollie.split('\n')
        
        extractionList.append(lines)
    
    for extractionNo, elist in enumerate(extractionList):
        if(len(elist)>1 and elist[1] != "No extractions found.\n"):
            #print elist
            sentenceToExtractionMap.update({extractionNo:elist})

    corefOutputList = xmlParseCorefResult(corenlpData.encode('utf-8','ignore'))      #call xml parser
    if(len(corefOutputList) != 0):
        corefPointerList = []
        listLen = len(corefOutputList)
        for i in range(listLen):
            l = corefOutputList[i]
            
            for j in range(len(l)):
                nounprolist = []
                c = l[j]
                pro = c[0][0]
                noun = c[1][0]
                start = c[0][3]
                end = c[0][4]
                sentence = c[0][1] #replace pro in sentence at start-end
                if primaryEntity in noun:
                	nounprolist.append(primaryEntity)
                else:
                	nounprolist.append(noun)
                nounprolist.append(pro)
                nounprolist.append(start)
                nounprolist.append(end)
                corefPointerList = sentencewiseCorefResultDict.get(sentence)
                if corefPointerList == None:
                    corefPointerList = []
                corefPointerList.append(nounprolist)
                sentencewiseCorefResultDict.update({sentence:corefPointerList})
    if(len(corefOutputList) == 0):
        print "No coreference found for "
    
    for sentNo in sentencewiseCorefResultDict.keys():
        corefPointerList = sentencewiseCorefResultDict.get(sentNo)
        for npl in corefPointerList:
            if len(npl) == 4:
                if npl[1].lower().strip() in primaryEntSet:
                    #print npl[1]
                    l = primaryEntDict.get(npl[1])
                    if l == None:
                        l = set()
                        l.add(npl[0])
                        primaryEntDict.update({npl[1]:l})     
                    else:
                        l.add(npl[0])
                        primaryEntDict.update({npl[1]:l})
    #print "ped " + str(primaryEntDict)
    for pi in primaryEntDict.keys():
        l = primaryEntDict.get(pi)
        if primaryEnt in l:
            for ent in l:
                setForReplacement.add(ent)
            setForReplacement.add(pi)
    dictlist = []
    dictlist.append(sentencewiseCorefResultDict)
    dictlist.append(sentenceToExtractionMap)
    filewiseInfoDict.update({key:dictlist})
        
    nounAfterDict = {}
    for dicts in filewiseInfoDict.keys():
        dictlist = filewiseInfoDict.get(dicts)
        sentencewiseCorefResultDict = dictlist[0]
        sentenceToExtractionMap = dictlist[1]           
        for sentNo in sentencewiseCorefResultDict.keys():
            corefPointerListFull = sentencewiseCorefResultDict.get(sentNo)
            multiPointerList,corefPointerList = multiplePronoun(corefPointerListFull)
            for nounprolist in corefPointerList:
                if len(nounprolist) != 0:    
                    noun = nounprolist[0].strip()
                    pronoun = nounprolist[1].strip()
                    # print "noun ", noun, " pronoun ", pronoun
                    extList = sentenceToExtractionMap.get(sentNo)
                    
                    if(extList != None):
                        #print "extList len ", len(extList)
                        for i in range(1,len(extList),1):       # all the extractions of a sentence. Replace in all the sentences.
                            line_i = extList[i]
                            score,ereList = getRelationAndEntity(line_i)
                            #print ereList
                            if(ereList != None):
                                if(len(word_tokenize(noun))>5):
                                    #print "noun before ", noun
                                    nounafter = nounAfterDict.get(noun)
                                    if nounafter == None:
                                        try:
                                            nounafter = getNounDependency(noun)#get strings connected to root word
                                            nounafter = nounafter.strip()
                                            nounAfterDict.update({noun:nounafter})
                                            noun = nounafter
                                            isReplace, l_index, w_index = ReplacingRules(ereList,noun,pronoun)
                                        except Exception,e:
                                            nounafter = ''
                                            isReplace = False
                                            l_index = 0
                                            w_index = 0
                                            #nounAfterDict.update({noun:nounafter})
                                            noun = nounafter
                                            print "len loop error",e    
                                    else:
                                        noun = nounafter
                                        isReplace, l_index, w_index = ReplacingRules(ereList,noun,pronoun)
                                    #print "noun after", noun

                                else:
                                    isReplace, l_index, w_index = ReplacingRules(ereList,noun,pronoun)
                                if(isReplace==True and w_index >=0):
                                    derefString = ereList[l_index]
                                    stringToken = word_tokenize(derefString)
                                    if noun in setForReplacement:
                                        stringToken[w_index]=primaryEnt
                                        replaceList.append([pronoun,primaryEnt])
                                    else:
                                        stringToken[w_index]=noun
                                        replaceList.append([pronoun,noun])
                                    
                                    ereList[l_index] = ' '.join(stringToken)
                                    newline_i = score+': ('+ereList[0] + ';'+ereList[1] + ';'+ereList[2] + ')'
                                    extList[i] = newline_i
                                elif(isReplace==True and w_index == -1):
                                    derefString = ereList[l_index]
                                    if noun in setForReplacement:
                                        replaceList.append([pronoun,primaryEnt])
                                        derefString = derefString.replace(pronoun,primaryEnt)
                                    else:
                                        replaceList.append([pronoun,noun])
                                        derefString = derefString.replace(pronoun,noun)
                                    
                                    ereList[l_index] = derefString
                                    newline_i = score+': ('+ereList[0] + ';'+ereList[1] + ';'+ereList[2] + ')'
                                    extList[i] = newline_i

                        sentenceToExtractionMap.update({sentNo:extList})

## This loop is for coref output of type: same pronoun--> multiple nouns in one sentence
            for mlist in multiPointerList:
                pronoun = mlist[0]
                noun1 = mlist[1]
                noun2  = mlist[2]
                start1 = mlist[3]
                start2 = mlist[4]
                extList = sentenceToExtractionMap.get(sentNo)
                if(extList != None):
                    for i in range(1,len(extList),1):       # all the extractions of a sentence. Replace in all the sentences.
                        line_i = extList[i]
                        score,ereList = getRelationAndEntity(line_i)
                        if(ereList != None):
                            noun = getProperNoun(pronoun,noun1,noun2,ereList,sentNo,corenlpData,start1,start2)
                            score,ereList = getRelationAndEntity(line_i)
                            if(ereList != None):
                                if noun == None:
                                    noun = noun1
                                isReplace, l_index, w_index = ReplacingRules(ereList,noun,pronoun)
                                if(isReplace==True and w_index >=0):
                                    derefString = ereList[l_index]
                                    stringToken = word_tokenize(derefString)
                                    if noun in setForReplacement:
                                        stringToken[w_index]=primaryEnt
                                        replaceList.append([pronoun,primaryEnt])
                                    else:
                                        stringToken[w_index]=noun
                                        replaceList.append([pronoun,noun])
                                        
                                    ereList[l_index] = ' '.join(stringToken)
                                    newline_i = score+': ('+ereList[0] + ';'+ereList[1] + ';'+ereList[2] + ')'
                                    extList[i] = newline_i
                                elif(isReplace==True and w_index == -1):
                                    derefString = ereList[l_index]
                                    if noun in setForReplacement:
                                        derefString = derefString.replace(pronoun,primaryEnt)
                                        replaceList.append([pronoun,primaryEnt])
                                    else:
                                        derefString = derefString.replace(pronoun,noun)
                                        replaceList.append([pronoun,noun])
                                        
                                    ereList[l_index] = derefString
                                    newline_i = score+': ('+ereList[0] + ';'+ereList[1] + ';'+ereList[2] + ')'
                                    extList[i] = newline_i
                    sentenceToExtractionMap.update({sentNo:extList})
  
        xmlfileName = str(dicts)
        storeInDb(sentenceToExtractionMap,sentencewiseCorefResultDict,xmlfileName)    
#######################################################
##           Write the outut to the files            ##
#######################################################
        # xmlfileName = str(dicts) +'.txt'
        # printToFile(sentenceToExtractionMap,sentencewiseCorefResultDict,xmlfileName)
    dbObj.client.close()
    collectEntities(primaryEntity, url)
	    
