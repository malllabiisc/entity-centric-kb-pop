import os
import xml
from xml.dom import minidom

class dependencyGraph():
    
    def __init__(self,name,objId,flag):
        self.name = name
        self.parent = None
        self.depObjList = []  
        if flag == 0:
            self.parent = objId
            self.depObjList = []
        if flag == 1:
            self.parent = None
            self.depObjList.append(objId)
            
    def updateObj(self,objId,flag):    
        if flag == 0:
            self.parent = objId
        if flag == 1:
            self.depObjList.append(objId)
        return self
    
def getDependencyList(filedata,senId):
    #senId = 1
    #filename = 'Nelson Mandela10.txt.xml'
    dependencyDict = {}
    deIdtoNameDict = {}
    governorDict = {}
    try:
        # print "file data type", type(filedata)
        xmldoc = xml.dom.minidom.parseString(filedata.encode('utf-8','ignore'))
        sentences = xmldoc.getElementsByTagName('sentences')[0]
        reqSentence = sentences.getElementsByTagName('sentence')[senId]
        dependencies = reqSentence.getElementsByTagName('dependencies')[0] #returns a list of things withing tag

        depList = dependencies.getElementsByTagName('dep')
        objList = []
        for i in range(len(depList)+200):
            objList.append(None)
    except Exception,e:
        print "no dep",e
        return None
    
    for dep in depList:
        #print "inside dep"
        dependentData = dep.getElementsByTagName('dependent')[0]
        dependentId = int(dependentData.getAttribute('idx'))
        #print "dep id"
        #print dependentId
        governorData = dep.getElementsByTagName('governor')[0]
        governorId = int(governorData.getAttribute("idx"))
        #print "gov id"
        #print governorId
        if(objList[dependentId] == None):
            dependent = str(dependentData.firstChild.data)
            depObj = dependencyGraph(dependent,governorId,0)
            objList[dependentId] = depObj
        else:
            depGraphObj = objList[dependentId]
            depGraphObj = depGraphObj.updateObj(governorId,0)
            objList[dependentId] = depGraphObj
            
        if(objList[governorId] == None):
            governor = str(governorData.firstChild.data)
            govObj = dependencyGraph(governor,dependentId,1)
            if(governorId == 0):
                govObj.parent = 0
            objList[governorId] = govObj
        else:
            govObj = objList[governorId]
            govObj = govObj.updateObj(dependentId,1)
            objList[governorId] = govObj
    return objList
    
