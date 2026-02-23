package com.yacl.bootstrap;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class FilesystemPathReadinessInitializer implements PathReadinessInitializer {

    private static final Logger log = LoggerFactory.getLogger(FilesystemPathReadinessInitializer.class);

    private final Path appRoot;

    public FilesystemPathReadinessInitializer(
            @Value("${yacl.app.root:${user.home}/.yacl}") String appRoot) {
        this.appRoot = Path.of(appRoot);
    }

    @Override
    public void initializePaths() {
        List<Path> required = List.of(
                appRoot,
                appRoot.resolve("data"),
                appRoot.resolve("cache"),
                appRoot.resolve("config"),
                appRoot.resolve("logs"));

        for (Path path : required) {
            try {
                Files.createDirectories(path);
                log.info("startup.phase=paths-ready path={}", path);
            } catch (Exception ex) {
                throw new IllegalStateException("Failed to prepare required path: " + path, ex);
            }
        }
    }
}
