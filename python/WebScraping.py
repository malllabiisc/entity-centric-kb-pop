#import python packages
import json
import urllib2
#import httplib2
import os
#import select
#import socket
import string
import nltk
from nltk import word_tokenize, pos_tag
from multiprocessing import Process, Queue
import time
from boilerpipe.extract import Extractor
from boilerpipeTextExtraction import getLinks_api_search,getLinks_cmu_search, getLinks_custom_search, extractDataFromLink

##
#read Keys
##
keys = {}
execfile("config/keys.txt", keys)
api_key = keys["api_key"]
cx_key = keys["cx_key"]


####
# entity - mid of the entity
# entType - entity type (freebase defined)
# returns attribute values of the specified enity
####
def getAttribValues(entity, entType):
    service_url = 'https://www.googleapis.com/freebase/v1/mqlread'
    query = [{  '*': None, 'mid': entity,  'type':entType }]
    params = {
            'query': json.dumps(query),
            'key': api_key
    }
    try:
        urls = service_url + '?' + urllib.urlencode(params)
        extractor = Extractor(extractor='ArticleExtractor', url=urls)
        extracted_text = extractor.getText()
        response = json.loads(extracted_text)
        return response
    except:
        #print "$$$$ERROR$$$"
        return None

##
# return the type json object.
# json object contains list of types defined for given entity
##
def getTypeListFromFreebase(entId):
    service_url = 'https://www.googleapis.com/freebase/v1/mqlread'
    query = [{  'mid': entId, 'name': [],  'type':[] }]

    params = {
            'query': json.dumps(query),
            'key': api_key
    }
    try:
        urls = service_url + '?' + urllib.urlencode(params)
        extractor = Extractor(extractor='ArticleExtractor', url=urls)
        extracted_text = extractor.getText()
        response = json.loads(extracted_text)
        return response
    except:
        return None


###############
# @args input
# entToSearch - primary entity to search for
# mid - freebase machine id of the entity
# queryStrings - supporting strings about primary entity. This is to improve search result.
###############
def webScraping(entToSearch, queryStrings):

    dirName=entToSearch;
    entTypeList = []

    tempSet = set()
    valuesToSearch = set()
    for q in queryStrings:
        valuesToSearch.add(q)

    valuesToSearch.add(entToSearch)

    fileCount = 1

    processList = []
    q = Queue()
    fileCount = 1;
    link_set = set()
    for qstr in valuesToSearch:
        if qstr == entToSearch:
            searchString = "\""+entToSearch+"\""
        else:
            qstr = qstr.strip('\n')
            searchString = entToSearch + " " + qstr
        print "ent to search" ,searchString
        linksList_api = getLinks_api_search(searchString,2)
        time.sleep(1)
        linksList_cstm = getLinks_custom_search(searchString)   #last int to control the number of links
        linksList_cmu = getLinks_cmu_search(searchString)
        #print "reminder--cmu search disabled"

        if linksList_api != None:
            for l in linksList_api:
                l = l.strip(' ')
                l = l.strip('\n')
                link_set.add(l)

        if linksList_cstm != None:
            for l in linksList_cstm:
                l = l.strip(' ')
                l = l.strip('\n')
                link_set.add(l)

        if linksList_cmu != None:
            for l in linksList_cmu:
                l = l.strip(' ')
                l = l.strip('\n')
                link_set.add(l)

        print "link count :",len(link_set)

    if link_set != None:
        for link in link_set:
            newProc = Process(target=extractDataFromLink, args=[q, link, entToSearch,fileCount])# call a function to do corenlp->sentcreate->ollie
            fileCount += 1;
            processList.append(newProc)
            newProc.start()
    for p in processList:
        p.join()
