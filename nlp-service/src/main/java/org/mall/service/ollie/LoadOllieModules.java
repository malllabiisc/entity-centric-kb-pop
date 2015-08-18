package org.mall.service.ollie;

import java.io.File;
import java.io.FileInputStream;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.util.Properties;

import opennlp.tools.cmdline.postag.POSModelLoader;
import opennlp.tools.postag.POSModel;
import opennlp.tools.tokenize.TokenizerModel;
import edu.knowitall.ollie.Ollie;
import edu.knowitall.tool.parse.MaltParser;
import edu.knowitall.tool.postag.OpenNlpPostagger;
import edu.knowitall.tool.tokenize.OpenNlpTokenizer;

public class LoadOllieModules {

	// the parser--a step required before the extractor
	private static MaltParser maltParser;
	// the path of the malt parser model file
	private static final String MALT_PARSER_FILE_PATH = "MALT_PARSER_FILE_PATH";
	private static String configFilename = "server.properties";
	private static String POS_FILE_PATH = "POS_FILE_PATH";
	private static String TOKEN_FILE_PATH = "TOKEN_FILE_PATH";
	
	private static POSModel posModel = null;
	private static OpenNlpTokenizer openNlpTokenizer = null;
	
	// the extractor itself
	private static Ollie ollie;
	static {
		// initialize MaltParser
		try {
			Properties config = new Properties();
			
			FileInputStream propertyFile = new FileInputStream(configFilename);
			
			
			config.load(propertyFile);
			System.out.println(config.getProperty(POS_FILE_PATH));
			System.out.println(config.getProperty(TOKEN_FILE_PATH));

			posModel = new POSModelLoader().load(new File(config
					.getProperty(POS_FILE_PATH)));
			//openNlpTokenizer = new OpenNlpTokenizer(
			//		config.getProperty(TOKEN_FILE_PATH));
			
			InputStream is = new FileInputStream(config.getProperty(TOKEN_FILE_PATH));
	    	TokenizerModel model = new TokenizerModel(is);
			openNlpTokenizer = new OpenNlpTokenizer(model);

			//			posModel = new POSModelLoader().load(new File("en-pos-maxent.bin"));
//			
//			InputStream is = new FileInputStream("en-token.bin");
//			TokenizerModel model = new TokenizerModel(is);
//			openNlpTokenizer = new OpenNlpTokenizer(model);
			
			scala.Option<File> nullOption = scala.Option.apply(null);

			maltParser = new MaltParser(new File(
					config.getProperty(MALT_PARSER_FILE_PATH)).toURI().toURL(),
					new OpenNlpPostagger(posModel, openNlpTokenizer),
					nullOption);
//			maltParser = new MaltParser(new File(MALT_PARSER_FILE_PATH).toURI().toURL(),
//					new OpenNlpPostagger(posModel, openNlpTokenizer),
//					nullOption);
			
		} catch (Exception e) {
			e.printStackTrace();
		}
		ollie = new Ollie();
	}

	public static Ollie getOllieObj() {
		return ollie;
	}

	public static MaltParser getMaltParserObj() {
		return maltParser;

	}

}
