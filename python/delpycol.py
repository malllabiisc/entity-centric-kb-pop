from pymongo import MongoClient
import mongodbClass as mdb

def deleteCollection(colName):
	c = MongoClient()
	#c['doc-database'].drop_collection('triples-collection')
	c['doc-database'].drop_collection(colName)

def deleteRecord(entName):
    # dbObj = mdb.mongodbDatabase('doc_collection')
    # col = dbObj.docCollection
    # col.delete_many({"primaryEnt":entName})

    # dbObj_tmp = mdb.mongodbDatabase('tmp_collection')
    # col_tmp = dbObj_tmp.docCollection
    # col_tmp.delete_many({"primaryEnt":entName})

    dbObj_final_c = mdb.mongodbDatabase('final_triples')
    col_final_triples = dbObj_final_c.docCollection
    col_final_triples.delete_many({'primaryEnt':entName})

    dbObj_final_triples = mdb.mongodbDatabase('cluster_info')
    col_final_triples = dbObj_final_triples.docCollection
    col_final_triples.delete_many({'primaryEnt':entName})


    dbObj_all_ext_collection_new = mdb.mongodbDatabase('all_ext_collection_new')
    col_all_ext_collection_new = dbObj_all_ext_collection_new.docCollection
    col_all_ext_collection_new.delete_many({'primaryEnt':entName})

    dbObj_triples_collection = mdb.mongodbDatabase('triples_collection')
    col_triples_collection = dbObj_triples_collection.docCollection
    triples = col_triples_collection.find({'primaryEnt':entName})
    ids = set()
    for triple in triples:
        ids.add(triple.get('_id'))
    for del_id in ids:
        col_triples_collection.delete_one({'_id':del_id})

entName = raw_input('Entity record to delete: ')
deleteRecord(entName)
