#import python packages
import json
import urllib2
import os
import string
import nltk
from nltk import word_tokenize, pos_tag
from multiprocessing import Process, Queue
import time
from boilerpipe.extract import Extractor
from boilerpipeTextExtraction import getLinks_api_search,getLinks_cmu_search, getLinks_custom_search, extractDataFromLink

########################################################################################
# Enter primary entity name. Give supporting strings and/or freebase id.
########################################################################################
from getEntities import collectEntities
from clusterAndNormalise import entityClusterAndNormalise
from dereferenceOllieOutput_new import ReplaceCorefPointers
from ent_linking_kb import inference_test
from WebScraping import webScraping

def Main(filename):
    entLine = open(filename).readlines()
    que = Queue()
    entProDict = {}
    proList = []
    entList = []
    for e in entLine:
        print e
        entLineList = e.split(',')
        entToSearch = entLineList[0]
        entList.append(entToSearch)

        queryStrings = []

        for i in range(1,len(entLineList),1):
            queryStrings.append(entLineList[i])

        #webScraping(entToSearch, queryStrings)

    for ent in entList:
        ReplaceCorefPointers(ent)
        collectEntities(ent)
        entityClusterAndNormalise(ent)
        success = inference_test(ent)  
    return success

inputfile = raw_input('file name')
Main(inputfile)

#'input/input.txt'
