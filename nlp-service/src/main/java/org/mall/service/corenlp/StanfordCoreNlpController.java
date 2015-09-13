package org.mall.service.corenlp;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import nu.xom.Serializer;

import org.apache.log4j.Logger;


import edu.stanford.nlp.ling.CoreAnnotations;
import edu.stanford.nlp.pipeline.Annotation;
import edu.stanford.nlp.pipeline.StanfordCoreNLP;
import edu.stanford.nlp.pipeline.XMLOutputter;
import edu.stanford.nlp.trees.Tree;
import edu.stanford.nlp.trees.TreeCoreAnnotations;
import edu.stanford.nlp.util.CoreMap;
import java.io.StringReader;
import java.io.StringWriter;
 
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
 
import org.restexpress.Request;
import org.restexpress.Response;
import org.w3c.dom.Document;
import org.xml.sax.InputSource;

import scala.util.control.Exception.Catch;




public class StanfordCoreNlpController {
	
	private static final Logger logger = Logger.getLogger(StanfordCoreNLP.class);
	private static final String DATA_PARAM_KEY = "data";

	private void allowCORS(Response response) {
		response.addHeader("Access-Control-Allow-Origin", "*");
		response.addHeader("Access-Control-Allow-Methods", "*");
		response.addHeader("Access-Control-Allow-Headers", "*");
	}
	
	private static Document convertStringToDocument(String xmlStr) {
        DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance(); 
        DocumentBuilder builder; 
        try 
        { 
            builder = factory.newDocumentBuilder(); 
            Document doc = builder.parse( new InputSource( new StringReader( xmlStr ) ) );
            return doc;
        } catch (Exception e) { 
            e.printStackTrace(); 
        }
        return null;
    }
	public Map<String, Object> create(Request request, Response response)
			throws Exception {
		logger.info("Request remote address : " + request.getRemoteAddress()
				+ "; X-FORWARDED_FOR : " + request.getHeader("X-FORWARDED-FOR"));
		Map<String, Object> responseParams = new HashMap<String, Object>();
		allowCORS(response);
		Map<String, List<String>> requestParams = request
				.getBodyFromUrlFormEncoded();
		logger.info("Request Params : " + requestParams.toString());
		if (requestParams.get(DATA_PARAM_KEY) == null) {
			responseParams.put("Status", "data parameter missing");
		} 
		else {	
			// text that needs to be processed by corenlp
			String data = requestParams.get(DATA_PARAM_KEY).get(0);   
			
			Annotation annotation = null;
		    StanfordCoreNLP pipeline = LoadStanfordModules.getPipelineObj();			
			try{
			    annotation = new Annotation(data);
			    pipeline.annotate(annotation);
			}
			catch(Exception e){
				e.printStackTrace();
				System.out.println(data);
			}
		    // get the corenlp xml output and construct a string that is returned as a response to client
		    nu.xom.Document xmldoc = XMLOutputter.annotationToDoc(annotation, pipeline);
			 // below is a tweaked version of XMLOutputter.writeXml()
			 ByteArrayOutputStream sw = new ByteArrayOutputStream();
			 Serializer ser = new Serializer(sw);
			     ser.setIndent(0);
			     ser.setLineSeparator("\n"); // gonna kill this in a moment
			     try {
					ser.write(xmldoc);
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			     try {
					ser.flush();
				} catch (IOException e) {
					// TODO Auto-generated catch block
					e.printStackTrace();
				}
			 String xmlStr = sw.toString();
			 Document doc = convertStringToDocument(xmlStr);
			 		    
		    responseParams.put("xmlOutput", xmlStr);
			responseParams.put("Status", "SUCCESS");
		}
		return responseParams;
		}
    
   }

