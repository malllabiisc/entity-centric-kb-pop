package org.mall.service.corenlp;

import java.util.Properties;

import edu.stanford.nlp.pipeline.StanfordCoreNLP;

public class LoadStanfordModules{
	
	private static StanfordCoreNLP pipeline;
	static{
		Properties props = new Properties();
	    props.setProperty("annotators", "tokenize, ssplit, pos, lemma, parse, sentiment, ner, dcoref");
	    pipeline = new StanfordCoreNLP(props);
	}
		
	public static StanfordCoreNLP getPipelineObj(){
		return pipeline;
	}
	
}
