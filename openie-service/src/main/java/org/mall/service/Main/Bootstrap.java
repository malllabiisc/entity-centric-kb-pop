/**
 * @author yogesh.dahiya
 */
package org.mall.service.Main;

import org.apache.log4j.Logger;

import io.netty.handler.codec.http.HttpMethod;

import org.restexpress.RestExpress;
import org.restexpress.pipeline.SimpleConsoleLogMessageObserver;

public class Bootstrap {

	private static final Logger logger = Logger.getLogger(Bootstrap.class);

	public static void main(String args[]) {
		try {
			/*
			 * loading class before starting server so that nlp-service cache gets
			 * loaded
			 */
			Class.forName("org.mall.service.openie.openIELoadModules");
			/* */
			logger.info("init succesful");
			Configuration config = new Configuration();
			RestExpress server = new RestExpress().setName(config.getName())
					.setPort(config.getPort())
					.addMessageObserver(new SimpleConsoleLogMessageObserver())
					.setExecutorThreadCount(config.getExecutorThreadCount())
					.setIoThreadCount(config.getWorkerCount())
					.setMaxContentSize(config.getRequestMaxContentLength());
			defineRoutes(server, config);
			server.bind();
			server.awaitShutdown();
		} catch (Exception ex) {
			logger.error("error initializing server " + ex);
		}
	}

	private static void defineRoutes(RestExpress server, Configuration config) {
		server.uri("/openie", config.getOpenieController()).action("create",
				HttpMethod.POST);
	}
}
