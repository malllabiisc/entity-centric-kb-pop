package org.mall.service.openie;

import edu.knowitall.openie.OpenIE;
import edu.knowitall.tool.parse.ClearParser;
import edu.knowitall.tool.postag.ClearPostagger;
import edu.knowitall.tool.srl.ClearSrl;
import edu.knowitall.tool.tokenize.ClearTokenizer;

public class openIELoadModules {
	private static OpenIE openIE;
	static{	
		openIE = new OpenIE(new ClearParser(new ClearPostagger(
	            new ClearTokenizer(ClearTokenizer.defaultModelUrl()))),
	            new ClearSrl(), false);
		
	}

public static OpenIE getOpenIE(){
	return openIE;
	}
}
