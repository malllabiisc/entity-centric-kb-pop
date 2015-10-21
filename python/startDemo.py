from flask import Flask,url_for,request, jsonify
from flask import render_template
from flask import request
import pymongo
from pymongo import MongoClient
from entityDetails import Main
from fileReader import getList
import sys
import re
import solr
import nltk
from nltk import word_tokenize, pos_tag

app = Flask(__name__)
app.config.update(
    threaded=True,
    DEBUG=False,
    PROPAGATE_EXCEPTIONS=True
)

app.entSearch1 = ''
class mongodbDatabase:
    'this class handles all the write and read operations related to doc-database'
    # variable to store the total number of entities scraped.
    entityCount = 0

    def __init__(self, collectionName):
        config = {}
        execfile("config/database.txt", config)
        self.ip = config["ip"]
        self.port = config["port"]

        self.client = MongoClient(self.ip, self.port)
        self.documentDatabase = self.client[config["database"]]
        self.docCollection = self.documentDatabase[config[collectionName]]
    
    ## this method returns all the documents downloaded for a given entity as a list.
    def getDocuments(primaryEnt):
        documentsList = []

def getFreebaseId(ent):
    #connection
    conn = solr.SolrConnection('http://localhost:8983/solr')
    # do a search
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
                return hit['author']
    except Exception,e:
        print e
        return None

def getType(ent):
    dbObj = mongodbDatabase('ent_type_collection')
    col = dbObj.docCollection
    val = col.find_one({'ent':ent})
    if val != None:
        return [val.get('ent'),val.get('type')]
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
                    return [t.get('ent'),t.get('type')]
            except Exception,e:
                dbObj.client.close()
                print "GetType Error",e
                return None
    dbObj.client.close()
    return None

##############################################
##############################################
### page redirections
##############################################
##############################################
@app.route("/nellpage")
def gotoNellPage():
    selectedEnt = request.args.get('data')
    if selectedEnt != None:
        ent2 = selectedEnt.split(',')[3]
        entType = getType(ent2)
        


@app.route("/moreinfo")
def moreinfopage():
    fact = request.args.get('moreinf')
    entSearch = app.entSearch1.strip()
    print "fact", fact
    if len(fact)>=6:
        fact = fact.encode('utf-8','ignore')
        print "type of fact",type(fact)
        factList = fact.split(',')
        ent2 = factList[3]
        linktoInfoPage = str(factList[5].strip().strip('\n').strip("'"))
        clusterID = str(factList[6].strip().strip("'"))
        cluster_obj = mongodbDatabase('cluster_info')
        cluster_col = cluster_obj.docCollection
        
        # if freebaseid != None:
        #     freebaseurl = "https://www.freebase.com"+freebaseid
        #     print "freebase url ", freebaseurl
        

        if linktoInfoPage != None:        
            print "link="+str(linktoInfoPage), "linktype", type(linktoInfoPage)
            print "clusterid="+str(clusterID), "cid type ", type(clusterID)
            print "primaryEnt="+str(entSearch)
            oldVal = cluster_col.find_one({'primaryEnt':entSearch, 'url':linktoInfoPage, 'key':clusterID})
            if oldVal == None:
                print "No extractions--"
                return render_template('errorPage.html', error="No info available")
            else:
                data = oldVal.get('similar_facts')
                allSimFacts = []
                for d in data:
                    facts = ','.join(d).encode('utf-8','ignore') + "\n"
                    allSimFacts.append(facts)
                return render_template('moreinfopage.html', data=allSimFacts, url = linktoInfoPage)
        else:
            return render_template('errorPage.html', error="No info available")


@app.route("/page2")
def page2():
    # newProc = Process(target=extractDataFromLink, args=[q, link, entToSearch,fileCount])# call a function to do corenlp->sentcreate->ollie
    # fileCount += 1;
    # processList.append(newProc)
    # newProc.start()
    # for p in processList:
    #     p.join()

    entToSearch = request.args.get('fname')
    abc = entToSearch
    app.entSearch1 = entToSearch
    queryStrings = request.args.get('qname')
    queryWords = []
    for q in queryStrings.split(','):
        queryWords.append(q)
    
    outputFileName = 'output/'+entToSearch.replace(' ','_') +'.csv'
    try:
      success = Main(entToSearch,queryWords)
    except Exception,e:
      success = False
      print e

    if success:
        mappedTriplesObj = mongodbDatabase('nell_mapped_triples_collection')
        nellMapCol = mappedTriplesObj.docCollection
        mappedTriples = nellMapCol.find_one({'primaryEnt':entToSearch})
        if mappedTriples != None:
            mappedTriplesList = mappedTriples.get('mapped-triples')
            print "type0 ", type(mappedTriplesList)
            print "type1 ", type(mappedTriplesList[0][0])
            output = []
            for mt in mappedTriplesList:
                l = []
                for mp in mt:
                    x = mp.encode('utf-8','ignore')
                    l.append(x)
                output.append(l)
            print "output type ", type(output[0][0]), "value ",output[0][0]
        mappedTriplesObj.client.close()
        return render_template('entDetailsOutput.html', output=output, enumerate=enumerate)
        
        # 0     1       2           3       4       5               6           7
        # ent1, rel, nellrelation, ent2, exttype, urlof data ext, clusterid, nellurl       
    else:
        return render_template('errorPage.html', error="No info available")

@app.route('/_status_update')
def status_update():
    print "In status Update"
    entSearch = request.args.get('entitySearch')
    statusDict = {}
    data1 = []
    dbObj = mongodbDatabase('doc_collection')
    col = dbObj.docCollection
    downloaded = col.find({'primaryEnt':entSearch})
    if downloaded != None:
        for d in downloaded:
            url = d.get('url').encode('utf-8','ignore')
            data1.append(url)
    statusDict.update({'download':data1})
    dbObj.client.close()
    dbObj = mongodbDatabase('tmp_collection')
    col = dbObj.docCollection
    data2 = []
    downloaded = col.find({'primaryEnt':entSearch})
    if downloaded != None:
        for d in downloaded:
            url = d.get('url').encode('utf-8','ignore')
            data2.append(url)
    statusDict.update({'coref-openie':data2})
    dbObj.client.close()
    dbObj = mongodbDatabase('final_triples')
    col = dbObj.docCollection
    data3 = []
    downloaded = col.find({'primaryEnt':entSearch})
    if downloaded != None:
        for d in downloaded:
            url = d.get('url').encode('utf-8','ignore')
            data3.append(url)
    statusDict.update({'cluster':data3})
    
    return jsonify(result=statusDict)

@app.route("/")
def page1():
	#return render_template('page1.html',form=form)
	return render_template('startDemo.html')

