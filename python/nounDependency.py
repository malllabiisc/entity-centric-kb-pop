import os
import xml
from xml.dom import minidom
from random import randint
import json
import sys
import string
import socket
import urllib2
import urllib
import xml.etree.ElementTree as ET
import xml.etree.ElementTree
from xml.parsers import expat
import nltk
from nltk import word_tokenize, pos_tag
from clusterAndNormalise import JKFilterForNoun
config = {}
execfile("config/config.txt", config) 
    
def getNounDependency(noun):
    dependencyDict = {}
    deIdtoNameDict = {}
    governorDict = {}
    wordposDict = {}

    method = "POST"
    corenlpService1 = config["corenlp1"]
    corenlpService = corenlpService1
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
    noun = noun.encode('ascii','ignore')
    data = urllib.urlencode({'data': noun})
    request = urllib2.Request(corenlpService, data=data, headers={'Content-type': 'text/plain'})
    depList = []
    try:
        connection = opener.open(request, timeout=50)
        if connection.code == 200:
            data = connection.read()
            data = data.replace('&lt;',"<")
            data = data.replace('&gt;','>')           
            corefdata = json.loads(data)
            corefdata = corefdata["xmlOutput"]
            xmldoc = xml.dom.minidom.parseString(corefdata)
            sentences = xmldoc.getElementsByTagName('sentences')[0]
            sen = sentences.getElementsByTagName('sentence')[0]
            
            constructSentence = ''
            tokens = sen.getElementsByTagName('tokens')[0]
            t = tokens.getElementsByTagName('token')
            k=1
            for w in t:
                wordMeta = w.getElementsByTagName('word')
                word = str(wordMeta[0].firstChild.data)
                posMeta = w.getElementsByTagName('POS')
                pos = str(posMeta[0].firstChild.data)
                wordposDict.update({k:[word,pos]})
                k = k + 1
            dependencies = sen.getElementsByTagName('dependencies')[0] #returns a list of things withing tag

            depList = dependencies.getElementsByTagName('dep')
            connection.close()
    except urllib2.HTTPError,e:
        connection = e
        print "coref error", e.read()
        connection.close()
    strLen = max(wordposDict.keys())

    resultStr = ''
    root = ''
    rootid = -1
    for dep in depList:
        dependentData = dep.getElementsByTagName('dependent')[0]
        dependentId = int(dependentData.getAttribute('idx'))
        governorData = dep.getElementsByTagName('governor')[0]
        governorId = int(governorData.getAttribute("idx"))
        governor = str(governorData.firstChild.data)
        if governorId == 0:
            root = str(dependentData.firstChild.data)
            rootid = dependentId
    
    resultStr = root
    i = rootid - 1
    count = 0
    while(i>0):
        result = wordposDict.get(i)
        if result != None:
            w1 = result[1]
            w0 = result[0]
            if(w1.startswith("NN") or w1 == "CD" or w1 == "JJ" or w1 == "CC" or w1 == "PRP"):
                resultStr = str(w0) + ' ' + resultStr
            else:
                break
        i -= 1
    
    i = rootid + 1
    count = 0
    while(i<= strLen):
        result = wordposDict.get(i)
        i += 1
        if result != None:
            w1 = result[1]
            w0 = result[0]
            if(w1.startswith("NN") or w1 == "CD" or w1 == "JJ" or w1 == "CC" or w1 == "PRP"):
                resultStr = resultStr +' '+ str(w0)
                count += 1
            else:
                break
    #print "resultStr", resultStr
    retVal = JKFilterForNoun(resultStr,0)    
    if retVal[0] == True:
        return retVal[1]
    return ''
    
##n = getNounDependency('the only Jewish child in the school')
##print n