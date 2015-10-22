from flask import Flask,url_for,request, jsonify,session
from flask import render_template
from flask import request,redirect
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
    DEBUG=True,
    PROPAGATE_EXCEPTIONS=True
)

entSearch = ''
app.secret_key = 'xxx'

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
@app.route("/datapage")
def gotoNellPage():
    entSearch = request.args.get('entSearch')
    if entSearch != None:
        mappedTriplesObj = mongodbDatabase('nell_mapped_triples_collection')
        nellMapCol = mappedTriplesObj.docCollection
        mappedTriples = nellMapCol.find_one({'primaryEnt':entSearch})
        if mappedTriples != None:
            mappedTriplesList = mappedTriples.get('mapped-triples')
            output = []
            for mt in mappedTriplesList:
                l = []
                for mp in mt:
                    x = mp.encode('utf-8','ignore')
                    l.append(x)
                output.append(l)
        mappedTriplesObj.client.close()
        return render_template('entDetailsOutput.html', output=output, enumerate=enumerate,entSearch=entSearch)
    else:
    	return render_template('errorPage.html', error="No info available")
        
@app.route("/moreinfo")
def moreinfopage():
    global entSearch
    print "ent search",entSearch
    fact = request.args.get('moreinf')
    print "fact", fact
    entSearch = request.args.get('entSearch')
    if len(fact)>=6:
		fact = fact.encode('utf-8','ignore')
		print "type of fact",type(fact)
		factList = fact.split(',')
		ent2 = factList[3]
		linktoInfoPage = str(factList[5].strip().strip('\n').strip("'"))
		clusterID = str(factList[6].strip().strip("'"))
		cluster_obj = mongodbDatabase('cluster_info')
		cluster_col = cluster_obj.docCollection
		if linktoInfoPage != None:
			print "link="+str(linktoInfoPage), "linktype", type(linktoInfoPage)
			print "clusterid="+str(clusterID), "cid type ", type(clusterID)
			print "primaryEnt="+entSearch
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
					return render_template('moreinfopage.html', data=allSimFacts, url = linktoInfoPage,  entSearch=entSearch)
		else:
			return render_template('errorPage.html', error="No info available")


@app.route("/page2")
def page2():
    global entSearch
    entSearch = request.args.get('fname')
    session['entsearch'] = entSearch
    # app.entSearch = entSearch
    queryStrings = request.args.get('qname')
    queryWords = []
    for q in queryStrings.split(','):
        queryWords.append(q)
    
    outputFileName = 'output/'+entSearch.replace(' ','_') +'.csv'
    try:
      success = Main(entSearch,queryWords)
    except Exception,e:
      success = False
      print e

    if success:
        mappedTriplesObj = mongodbDatabase('nell_mapped_triples_collection')
        nellMapCol = mappedTriplesObj.docCollection
        mappedTriples = nellMapCol.find_one({'primaryEnt':entSearch})
        if mappedTriples != None:
            mappedTriplesList = mappedTriples.get('mapped-triples')
            output = []
            for mt in mappedTriplesList:
                l = []
                for mp in mt:
                    x = mp.encode('utf-8','ignore')
                    l.append(x)
                output.append(l)
        mappedTriplesObj.client.close()
        return render_template('entDetailsOutput.html', output=output, enumerate=enumerate,entSearch=entSearch)
        
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

@app.route('/clear')
def clearsession():
    # Clear the session
    session.clear()
    # Redirect the user to the main page
    return redirect(url_for('page1'))

@app.route("/")
def page1():
	# app.entSearch = ''
	print "new search started"
	entSearch = ''
	return render_template('startDemo.html')

