/**
 * @author yogesh.dahiya
 */
package org.mall.service.Main;



import org.mall.service.openie.OpenieController;
import org.restexpress.Format;
import org.restexpress.RestExpress;


import java.io.FileInputStream;
import java.util.Properties;
import org.apache.log4j.Logger;


public class Configuration {
	private static final Logger logger = Logger.getLogger(Configuration.class);
	private static final String NAME_PROPERTY = "SERVER_NAME";
	private static final String PORT_PROPERTY = "SERVER_PORT";
	private static final String WORKER_COUNT_PROPERTY = "SERVER_WORKER_THREAD_COUNT";
	private static final String EXECUTOR_THREAD_COUNT_PROPERTY = "SERVER_EXECUTOR_THREAD_COUNT";
	private static final String SERVER_REQUEST_MAX_CONTENT_LENGTH= "SERVER_REQUEST_MAX_CONTENT_LENGTH";
	
	private static final String serverConfigFilename = "server.properties";

	private static final int DEFAULT_WORKER_COUNT = 0;
	private static final int DEFAULT_EXECUTOR_THREAD_COUNT = 0;

	private int port;
	private String name;
	private String defaultFormat;
	private int workerCount;
	private int executorThreadCount;
	private int requestMaxContentLength;
	
	private OpenieController openieController = new OpenieController();   
			
	public OpenieController getOpenieController(){
		return openieController;
	}
	
	public Configuration() throws Exception {
		Properties serverProperties = new Properties();
						
		FileInputStream propertyFile = new FileInputStream(serverConfigFilename);
		serverProperties.load(propertyFile);
				
		this.name = serverProperties.getProperty(NAME_PROPERTY);
		this.port = Integer.parseInt(serverProperties.getProperty(
				PORT_PROPERTY, String.valueOf(RestExpress.DEFAULT_PORT)));
		this.workerCount = Integer.parseInt(serverProperties.getProperty(
				WORKER_COUNT_PROPERTY, String.valueOf(DEFAULT_WORKER_COUNT)));
		this.executorThreadCount = Integer.parseInt(serverProperties
				.getProperty(EXECUTOR_THREAD_COUNT_PROPERTY,
						String.valueOf(DEFAULT_EXECUTOR_THREAD_COUNT)));
		this.requestMaxContentLength=Integer.parseInt(serverProperties.getProperty((SERVER_REQUEST_MAX_CONTENT_LENGTH)));
	}
	public int getRequestMaxContentLength() {
		return requestMaxContentLength;
	}

	public String getDefaultFormat() {
		return defaultFormat;
	}

	public int getPort() {
		return port;
	}

	public String getName() {
		return name;
	}

	public int getWorkerCount() {
		return workerCount;
	}

	public int getExecutorThreadCount() {
		return executorThreadCount;
	}
}
