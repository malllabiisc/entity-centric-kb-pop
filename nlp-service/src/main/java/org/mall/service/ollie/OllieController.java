package org.mall.service.ollie;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;
import java.util.regex.Pattern;

import org.mall.service.ollie.LoadOllieModules;
import opennlp.tools.postag.POSModel;

import org.apache.log4j.Logger;
import org.restexpress.Request;
import org.restexpress.Response;

import edu.knowitall.ollie.Ollie;
import edu.knowitall.ollie.OllieExtraction;
import edu.knowitall.ollie.OllieExtractionInstance;
import edu.knowitall.tool.parse.MaltParser;
import edu.knowitall.tool.parse.graph.DependencyGraph;


/**
* Gets Ollie extractions from a single sentence.
* @param sentence
* @return the set of ollie extractions
*/

public class OllieController {

	private static final Logger logger = Logger.getLogger(OllieController.class);
	private static final String DATA_PARAM_KEY = "data";
	private static final String DELIMITER_PARAM_KEY = "del";
	
	private static MaltParser maltParser = LoadOllieModules.getMaltParserObj();
	private static Ollie ollie = LoadOllieModules.getOllieObj();
	
	private void allowCORS(Response response) {
		response.addHeader("Access-Control-Allow-Origin", "*");
		response.addHeader("Access-Control-Allow-Methods", "*");
		response.addHeader("Access-Control-Allow-Headers", "*");
	}
	
	public Iterable<OllieExtractionInstance> extract(String sentence) {
		Iterable<OllieExtractionInstance> extrs = null;
		try{
		// parse the sentence
			DependencyGraph graph = maltParser.dependencyGraph(sentence);
			// run Ollie over the sentence and convert to a Java collection
			extrs = scala.collection.JavaConversions.asJavaIterable(ollie.extract(graph));
			
		}catch(Exception e){
			logger.error("error sentence is "+sentence);
		}
		
		return extrs;
	}
		
	public Map<String, Object> create(Request request, Response response)
			throws Exception {
		String output = "";
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
			String delimiter = null;
			if(requestParams.get(DELIMITER_PARAM_KEY) != null)
				delimiter = requestParams.get(DELIMITER_PARAM_KEY).get(0);
			
			if(delimiter == null){
				if(data != null){
					output = output.concat(data+"\n");
					Iterable<OllieExtractionInstance> extrs = extract(data);
					if(extrs != null){
						for (OllieExtractionInstance inst : extrs) {
							OllieExtraction extr = inst.extr();
							output = output.concat(extr.openparseConfidence()+": (" +extr.arg1().text() + ";" + extr.rel().text()
									+ ";" + extr.arg2().text()+")"+"\n");
						}
					}
					else{
						output = output.concat("No extractions found.");
					}
					output = output.concat("\n");
				}
				
			}
			else{
				//StringTokenizer st = new StringTokenizer(data, "\\<\\T\\A\\B\\>");
				String [] sents = data.split(Pattern.quote(delimiter));
				//while(st.hasMoreTokens()){
				for(String st: sents){
				    String sentence = st; //(String) st.nextElement();
					if(sentence != null){
						output = output.concat(sentence+"\n");
						Iterable<OllieExtractionInstance> extrs = extract(sentence);
						if(extrs != null){
							for (OllieExtractionInstance inst : extrs) {
								OllieExtraction extr = inst.extr();
								output = output.concat(extr.openparseConfidence()+": (" +extr.arg1().text() + ";" + extr.rel().text()
										+ ";" + extr.arg2().text()+")"+"\n");
							}
						}
						else{
							output = output.concat("No extractions found.");
						}
							output = output.concat("--end of sentence--");
							output = output.concat("\n");
					}
				}	
			
			}
			
		    responseParams.put("ollieOutput", output);
			responseParams.put("Status", "SUCCESS");
		}
		return responseParams;
	}
}
