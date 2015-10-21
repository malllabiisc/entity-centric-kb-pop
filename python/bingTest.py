import urllib
import urllib2
import json

 
keyBing = 'dxmMM6XYsidMYjbK01JvaIJgX69LImGrnIDpspw3Gn8='
username = '3d295bea-cd5d-40d9-a709-fc068c93be06'
credentialBing = 'Basic ' + (':%s' % keyBing).encode('base64')[:]
searchString = '%27Xbox+One%27'
searchfor = "Xbox one"
top = 20
offset = 0
search_type = "Web"

#url = 'https://api.datamarket.azure.com/Bing/Search/Image?' + \
#     'Query=%s&$top=%d&$skip=%d&$format=json' % (searchString, top, offset)

url = 'http://api.datamarket.azure.com/Data.ashx/Bing/Search/'+search_type
print url

query = urllib.urlencode({'q': searchfor, top:10})

request_url = url + '?' + query

hits=[];
try:
	headers = {'User-Agent' : 'Mozilla/5.0', 'Content-type': 'application/json', 'Authorization': credentialBing,'Proxy-Connection': 'Keep-Alive',}
	req = urllib2.Request(request_url,None, headers)
	req_res = urllib2.urlopen(req).read()
	print "request_url ", request_url
	print req_res
except Exception,e:
	print "error ===> ",e
	
queryBingFor = "'google fibre'" # the apostrophe's required as that is the format the API Url expects. 
quoted_query = urllib.quote(queryBingFor)

rootURL = "http://api.datamarket.azure.com/Bing/Search/"
searchURL = rootURL + "Web?$format=json&Query=" + quoted_query

password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
password_mgr.add_password(None, searchURL,username,keyBing)

handler = urllib2.HTTPBasicAuthHandler(password_mgr)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)
readURL = urllib2.urlopen(searchURL).read()
print readURL
