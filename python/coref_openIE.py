import json
import sys
import os
import re
import string
import xml
from xml.dom import minidom
import socket
import urllib2
import urllib
import xml.etree.ElementTree as ET
import xml.etree.ElementTree as ElementTree
from xml.parsers import expat
import mongodbClass as mdb
from random import randint
from dereferenceOllieOutput import ReplaceCorefPointers

currentUrl = ''
primaryEnt = ''
openieInput = "inputForOllie"
corefOutput = "corefOutputFolder"
config = {}
execfile("config/config.txt", config)
# python 3: exec(open("example.conf").read(), config)

dbObj = None

def find(str, ch):
    for i, ltr in enumerate(str):
        if ltr == ch:
            yield i

def getRelationAndEntity(line):
    line = line.replace('[', ' ')
    line = line.replace(']',' ')
    start = line.find(':');                         #ollie output format = confidence: (ent1;rel;ent2)
    if start > 0:
        prob = line[0:start]                           #capture the confidence of the extraction
        extractionStart = line.find('(');              #start of ent1 after '('
        entities =  list(find(line,';'));              #ent and rel are separated by ';' so get all those indexes.
        if extractionStart > 0 and len(entities)>1:
            ent1 = line[extractionStart+1:entities[0]];    #get ent1 which is between ( and ;
            rel1 = line[entities[0]+1:entities[1]];        #get rel which is between ; and ;
            if len(entities) == 2:
                ent2 = line[entities[1]+1:];        #get ent2 which is between ; and end of line-1
            elif len(entities) > 2:
                ent2 = line[entities[1]+1:entities[2]];
            #ent2 = ent2.strip(')')
            return prob + " :(" + ent1 + ";" + rel1 +";" + ent2+ ")"
    return None;

def json2xml(json_obj, line_padding=""):
    result_list = list()

    json_obj_type = type(json_obj)

    if json_obj_type is list:
        for sub_elem in json_obj:
            result_list.append(json2xml(sub_elem, line_padding))

        return "\n".join(result_list)

    if json_obj_type is dict:
        for tag_name in json_obj:
            sub_obj = json_obj[tag_name]
            result_list.append("%s<%s>" % (line_padding, tag_name))
            result_list.append(json2xml(sub_obj, "\t" + line_padding))
            result_list.append("%s</%s>" % (line_padding, tag_name))

        return "\n".join(result_list)

    return "%s%s" % (line_padding, json_obj)


def xmlParseCorefResult_ET(xmldata):
    #try:
    #xmldoc = minidom.parse(filename) # coref output xml processed to get sentences
    doc = ET.ElementTree(ET.fromstring(xmldata.encode('utf-8','ignore')))
    document = doc.findall('document')[0]
    sentences = document.findall('sentences')[0]
    sentenceList = sentences.findall('sentence')
    #sentences = xmldoc.getElementsByTagName('sentences')[0] #returns a list of things withing tag
    #sentenceList = sentences.getElementsByTagName('sentence')
    constructedSenList = []
    for sen in sentenceList:
        constructSentence = ''
        #tokens = sen.getElementsByTagName('tokens')[0]
        tokens = sen.findall('tokens')[0]
        #t = tokens.getElementsByTagName('token')
        t = tokens.findall('token')
        for w in t:
            try:
                wordMeta = w.findall('word')
                #print "meta data",wordMeta[0].text
                word = (wordMeta[0].text).encode('utf-8','ignore')
            except Exception,e:
                word = '-LRB-'
                print "inside error",e

            if(word == ',' or word == '.'):
                constructSentence = constructSentence.strip(' ')
            if word != '-LRB-' or word != '-RRB-':
                constructSentence = constructSentence + str(word) + ' '

        constructSentence = constructSentence.strip(' ')
        constructSentence = constructSentence.strip(', u ` ')
        constructSentence = constructSentence.strip('\'')
        constructedSenList.append(constructSentence+'<TAB>')
    generateTriples(constructedSenList)
##    except Exception,e:
##        print "xml parse error",e
##        pass

#####
# read xml and construct sentence.
#####
def xmlParseCorefResult(xmldata):
    try:
        #xmldoc = minidom.parse(filename) # coref output xml processed to get sentences
        xmldoc = xml.dom.minidom.parseString(xmldata.encode('utf-8','ignore'))
        sentences = xmldoc.getElementsByTagName('sentences')[0] #returns a list of things withing tag
        sentenceList = sentences.getElementsByTagName('sentence')
        constructedSenList = []
        for sen in sentenceList:
            constructSentence = ''
            tokens = sen.getElementsByTagName('tokens')[0]
            t = tokens.getElementsByTagName('token')
            for w in t:
                wordMeta = w.getElementsByTagName('word')
                word = str(wordMeta[0].firstChild.data)
                if(word == ',' or word == '.'):
                    constructSentence = constructSentence.strip(' ')
                if word != '-LRB-' or word != '-RRB-':
                	constructSentence = constructSentence + str(word) + ' '

            constructSentence = constructSentence.strip(' ')
            constructSentence = constructSentence.strip(', u ` ')
            constructSentence = constructSentence.strip('\'')
            constructedSenList.append(constructSentence+'<TAB>')

        generateTriples(constructedSenList)
    except Exception,e:
        print "xml parse error",e, "for urls", currentUrl

def SentenceConstructionFromXML(corefdata):
    xmlParseCorefResult_ET(corefdata)

def getOllieFormat(openieList):
    modifiedList = []
    for ext in openieList:
        newLine = getRelationAndEntity(ext)
        modifiedList.append(newLine)
    return modifiedList

###########
# call ollie to generate triples
###########
def generateTriples(sentenceList):
    global dbObj
    openieDir="openieOutputFolder";
    openIEService4 = config["openie4"]
#    openIEService5 = config["openie5"]
#    if randint(0,1) == 1:
    openIEService = openIEService4
#    else:
#        openIEService = openIEService5

    method = "POST"
    handler = urllib2.HTTPHandler()
    opener = urllib2.build_opener(handler)
    openieOutputList = []
    chunkSize = 30
    for j in range(0, len(sentenceList),chunkSize):
        sentenceStr = ' '.join(sentenceList[j:j+chunkSize])
        # sentenceList = sentenceList.encode('utf-8')
        # print "open ie type: ", type(sentenceStr)
        data = urllib.urlencode({'data': sentenceStr, 'del':'<TAB>'})
        request = urllib2.Request(openIEService, data=data,  headers={'Content-type': 'text/plain'})
        # print "connecting ",openIEService
        try:
            connection = opener.open(request,timeout=60)
            if connection.code == 200:
                data = connection.read()
                openiedata = json.loads(data)
                openiedata = openiedata["openieOutput"]
                openieOutput = openiedata.split('--end of sentence--')
                for l in openieOutput:
                    openieOutputList.append(l.encode('utf-8','ignore'))
                print "openie done for", currentUrl
        except urllib2.HTTPError,e:
            connection = e
            print "openie error", e.read(), "for urls", currentUrl
            # connection.close()
    
    col = dbObj.docCollection
    oldVal = col.find_one({'url':currentUrl})
    corefdata = oldVal['corenlp']
    tmp_doc = {'url':currentUrl, 'primaryEnt':primaryEnt, 'openie':openieOutputList,'corenlp':corefdata}
    col.replace_one({'url':currentUrl},tmp_doc,True)
    connection.close()
    ReplaceCorefPointers(primaryEnt, currentUrl)

#########
# call coref resolution
# store the xml file generated.
# construct sentence from the file generated
#########
def corefResolution(sentenceList):
    global dbObj
    method = "POST"
    corenlpService = config["corenlp1"]

    # if randint(0,1) == 0:
    #     corenlpService = corenlpService1
    # else:
    #     corenlpService = corenlpService2
    # create a handler. you can specify different handlers here (file uploads etc)
    # but we go for the default
    handler = urllib2.HTTPHandler()
    # create an openerdirector instance
    opener = urllib2.build_opener(handler)
    # build a request
    sentenceList = sentenceList.encode('utf-8','ignore')
    data = urllib.urlencode({'data': sentenceList})
    request = urllib2.Request(corenlpService, data=data, headers={'Content-type': 'text/plain'})
    # print "trying to connect", corenlpService
    try:
        connection = opener.open(request, timeout=100)
        if connection.code == 200:
            data = connection.read()
            data = data.replace('&lt;',"<")
            data = data.replace('&gt;','>')

            corefdata = json.loads(data)
            corefdata = corefdata["xmlOutput"]
            col = dbObj.docCollection
            openiedata = ''
            tmp_doc = {'url':currentUrl, 'primaryEnt':primaryEnt, 'openie':openiedata, 'corenlp':corefdata}
            col.insert_one(tmp_doc)
            connection.close()
            print "coref done for", currentUrl
            # print "coref data type ", type(corefdata)
            SentenceConstructionFromXML(corefdata)
            #tree = ET.ElementTree(ET.fromstring(xmldata))
            #print tree.write('corefOutputFolder/'+xmlFile)
    except urllib2.HTTPError,e:
        connection = e
        print "coref error", e.read(), "for urls", currentUrl
        connection.close()


###########
# curFilename - filename  where xml output is stored
# sentenceList - data scraped
###########
def getTripleList(sentenceList,url,priEnt):
    global currentUrl
    global primaryEnt
    global dbObj
    dbObj = mdb.mongodbDatabase('tmp_collection')
    col = dbObj.docCollection

    currentUrl = url
    primaryEnt = priEnt
    if(col.find_one({'url':url,'primaryEnt':priEnt}) == None):
    	print "calling coref resolution for ",url
    	corefResolution(sentenceList)
    else:
        oldval = col.find_one({'url':url,'primaryEnt':priEnt})
        openieobj = oldval.get('openie')
        if len(openieobj) == 0 or openieobj == '':
            print "calling openie for", primaryEnt, "url ", url
            tmpobj = col.find_one({'url':url,'primaryEnt':priEnt})
            corefdata = tmpobj.get('corenlp')
            SentenceConstructionFromXML(corefdata)
    dbObj.client.close()

##datal = open('abc.txt','r').readlines()
##data = ' '.join(datal)
##getTripleList('xyz', data, 'wiki.com','xyz')
