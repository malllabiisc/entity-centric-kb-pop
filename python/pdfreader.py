import os
import urllib2
import urllib
from cStringIO import StringIO
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from coref_openIE import getTripleList

def convert(fname, pages=None):
    if not pages:
        pagenums = set()
    else:
        pagenums = set(pages)

    output = StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = file(fname, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text

# proxy_support = urllib2.ProxyHandler({"http":"proxy.iisc.ernet.in:3128"})
# opener = urllib2.build_opener(proxy_support)
# urllib2.install_opener(opener)
# URL = "https://www.iscp.ie/sites/default/files/pdf-sample.pdf"
# with open('filename','wb') as f:
#     f.write(urllib2.urlopen(URL).read())
#     f.close()

# content = convert('filename')
# content_txt = ''
# for w in content:
#     try:
#         w.decode('utf-8')
#         content_txt += w
#     except:
#         content_txt += ''

