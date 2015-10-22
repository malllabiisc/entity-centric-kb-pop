#!/usr/bin/python
import json
import urllib
import urllib2
import sys
import re
import os
import lxml.html
import nltk
import boilerpipe
import simplejson
from boilerpipe.extract import Extractor
from multiprocessing import Process, Queue
import time
import nltk.data
from xml.dom import minidom
#from processMultipleFiles import getTripleList
from coref_openIE import getTripleList
import pymongo
from pymongo import MongoClient
import mongodbClass as mdb
from pdfreader import convert

##
#read Keys
##
keys = {}
execfile("config/keys.txt", keys)
api_key = keys["api_key"]
cx_key = keys["cx_key"]
cmu_key = keys["cmu_key"]

##
#read urls
##
urlList = {}
execfile("config/urlList.txt", urlList)
cmu_search_url = urlList["cmu_search_url"]
api_search_url = urlList["api_search_url"]
cse_search_url = urlList["cse_search_url"]

minLen = 3
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

#####
# parse json to get the links from the response object
#####
def parseJson_custom_search(jsonString):
    hits = []
    response = json.loads(jsonString)
    if(response != None):
        resultList = response['items']
        for res in resultList:
            link = ""
            try:
                link = res['link']
                if res['pagemap']['metatags'][0]['og:type'] == "video":
                    link = ""
            except:
                if len(link) > 0:
                    hits.append(link)
    return hits



####
# searchfor - entity to be searched.
# use key, cx and query object to build the request
# parse response to get the links
####
def getLinks_custom_search(searchfor):

    params = {
            'key': api_key,
            'cx':cx_key,
            'q': searchfor
    }
    request_url = cse_search_url + '?' + urllib.urlencode(params)

    #print "url",request_url

    hits=[];
    try:
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(request_url, None, headers)
        req_res = urllib2.urlopen(req).read()
        hits = parseJson_custom_search(req_res)
    except Exception,e:
        print request_url
        print "cse error ", e
        return None

    if len(hits) == 0:
        print "No links received"
        return None
    return hits

#####
# parse json to get the links from the response object
#####
def parseJson_cmu_search(jsonString):
    hits = []
    response = json.loads(jsonString)
    if(response != None):
        try:
            resultList = response['results']
            for res in resultList:
                link = res['url']
                hits.append(link)
        except:
            return hits
    return hits


####
# searchfor - entity to be searched.
# use key, cx and query object to build the request
# parse response to get the links
####
def getLinks_cmu_search(searchfor):
    query = urllib.urlencode({'q': searchfor,'key': cmu_key})

    request_url = cmu_search_url + '?' + query

    hits=[];
    try:
        headers = { 'User-Agent' : 'Mozilla/5.0'}
        req = urllib2.Request(request_url, None, headers)
        req_res = urllib2.urlopen(req).read()
        hits = parseJson_cmu_search(req_res)
    except Exception,e:
        print request_url
        print "cmu error ", e
        return None

    if len(hits) == 0:
        print "No links received"
        return None
    return hits


def getLinks_api_search(searchfor, val):
    query = urllib.urlencode({'q': searchfor})
    url = api_search_url + query
    hits=[];
    num_queries = val*4
    try:
        for start in range(0, num_queries, 4):
            request_url = '{0}&start={1}'.format(url, start)
            headers = { 'User-Agent' : 'Mozilla/5.0' }
            req = urllib2.Request(request_url, None, headers)
            reqres = urllib2.urlopen(req).read()
            urlList = simplejson.loads(reqres)
            if(urlList != None):
                results = urlList['responseData']['results']
                for i in results:
                    hits.append(i['url'])
        return hits;
    except Exception,e:
        print "api error ", e
        return None

def cleanTheExtraction(extText):
    strent = ' '.join(extText.split())
    numbers = re.findall(r'\[([^]]*)\]',strent)
    if(len(numbers) !=0):
        for num in numbers:
            strent = strent.replace("["+num+"]","")
    strent = strent.replace('(','')
    strent = strent.replace(')','')
    return strent

##################
# extract the data from all the links given in urlList
# write the output to a file
# return file count
##################
def extractDataFromLink(queue, urls, filename, fileCount):
    dbObj = mdb.mongodbDatabase('doc_collection')
    docs = dbObj.docCollection
    down_doc = docs.find_one({'url':urls,'primaryEnt':filename})

    if(down_doc == None or (down_doc['documents'] == None) or len(down_doc['documents'])==0):
        try:
        #print "down load docs for ",urls
            cleanText = ''
            if(urls.endswith('.pdf')):
                print "############# found pdf #############"
                proxy_support = urllib2.ProxyHandler({"http":"proxy.iisc.ernet.in:3128"})
                opener = urllib2.build_opener(proxy_support)
                urllib2.install_opener(opener)
                with open('filename','wb') as f:
                    f.write(urllib2.urlopen(URL).read())
                    f.close()
                content = convert('filename')
                cleanText = content.encode('utf-8','ignore')
            else:
                extractor = Extractor(extractor='ArticleExtractor', url=urls)
                extracted_text = extractor.getText()
                cleanText = cleanTheExtraction(extracted_text)

            sentenceList = tokenizer.tokenize(cleanText)    #get sentences

            if(len(sentenceList) > minLen):           # write to a file if the extraction size is greater than min no. of sentences
                curFile = filename+str(fileCount)+'.txt'
                senList = []
                for l in sentenceList:
                    newl = l.encode('utf-8','ignore')
                    senList.append(newl)

                document = {'url': urls, 'documents':senList, 'primaryEnt':filename}
                if down_doc == None:
                    post_id = docs.insert_one(document) #.inserted_id
                else:
                    docs.replace_one({'url': urls, 'primaryEnt':filename},document,True)

                sentenceString = ' '.join(sentenceList)
                getTripleList(sentenceString,urls,filename)# call a function to do corenlp->sentcreate->ollie
        except Exception, e:
            print "error in boilerpipe code: ",e," url: ", urls
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
    else:
        try:
            oldVal = docs.find_one({'url':urls,'primaryEnt':filename})
            sentenceList = oldVal['documents']
            sentenceString = ' '.join(sentenceList)
            # print "Sentence string type: ", type(sentenceString)
            getTripleList(sentenceString,urls,filename)# call a function to do corenlp->sentcreate->ollie
        except Exception,e:
            print "error in retrieving doc for ", urls,e
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
    dbObj.client.close()
