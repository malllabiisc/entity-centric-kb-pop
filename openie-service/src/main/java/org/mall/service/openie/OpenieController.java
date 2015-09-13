package org.mall.service.openie;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.StringTokenizer;
import java.util.regex.Pattern;

import opennlp.tools.postag.POSModel;

import org.apache.log4j.Logger;
import org.restexpress.Request;
import org.restexpress.Response;

import scala.collection.Iterator;
import scala.collection.Seq;

import edu.knowitall.openie.*;
import edu.knowitall.tool.parse.ClearParser;
import edu.knowitall.tool.postag.ClearPostagger;
import edu.knowitall.tool.postag.Postagger;
import edu.knowitall.tool.srl.Argument;
import edu.knowitall.tool.srl.ClearSrl;
import edu.knowitall.tool.tokenize.ClearTokenizer;

/**
* Gets Ollie extractions from a single sentence.
* @param sentence
* @return the set of ollie extractions
*/

public class OpenieController {

	private static final Logger logger = Logger.getLogger(OpenieController.class);
	private static final String DATA_PARAM_KEY = "data";
	private static final String DELIMITER_PARAM_KEY = "del";
	private static OpenIE openIE = openIELoadModules.getOpenIE();
	
	private void allowCORS(Response response) {
		response.addHeader("Access-Control-Allow-Origin", "*");
		response.addHeader("Access-Control-Allow-Methods", "*");
		response.addHeader("Access-Control-Allow-Headers", "*");
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
			
			String[] sentences = null;
			if(delimiter == null){
				sentences = new String[1];
				sentences[0] = data;
			}
			else{
				sentences = data.split(Pattern.quote(delimiter));
			}
			for(String sentence:sentences){
				output = output.concat(sentence+"\n");
				Seq<Instance> extractions = openIE.extract(sentence);
		        Iterator<Instance> iterator = extractions.iterator();
		        while (iterator.hasNext()) {
		            Instance inst = iterator.next();
		            StringBuilder sb = new StringBuilder();
		            sb.append(inst.confidence())
		                .append(": (")
		                .append(inst.extr().arg1().text())
		                .append(';')
		                .append(inst.extr().rel().text())
		                .append(';')
		                .append(inst.extr().arg2s().toString());
		            	
		           /* 	
		            Iterator<Part> argIter = inst.extr().arg2s().iterator();
		            while (argIter.hasNext()) {
		                Part arg = argIter.next();
		                //Argument a = argIter.next();
		                sb.append(arg.text()).append("; ");
		            }
		            */
		            output = output.concat(sb.toString()+")\n");
				 }
		        output = output.concat("--end of sentence--"+"\n");
			 }
		  }						
		responseParams.put("openieOutput", output);
		responseParams.put("Status", "SUCCESS");
		return responseParams;
	}
}
