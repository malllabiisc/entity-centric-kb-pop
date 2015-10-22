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
# Main('Albert Einstein')
########################################################################################
from getEntities import collectEntities
from clusterAndNormalise import entityClusterAndNormalise
from dereferenceOllieOutput import ReplaceCorefPointers
from ent_linking_kb import inference_test
from WebScraping import webScraping

def Main(entToSearch,queryStrings):
    que = Queue()
    entProDict = {}
    proList = []
    entList = []
    entLineList = []
        
    webScraping(entToSearch, queryStrings)
    entityClusterAndNormalise(entToSearch)
    success = inference_test(entToSearch)
    return success

