import pymongo
from pymongo import MongoClient


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
		
    