package com.yacl.bootstrap.settings;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class FileSettingsInitializer implements SettingsInitializer {

    private static final Logger log = LoggerFactory.getLogger(FileSettingsInitializer.class);

    private final Path configDir;
    private final ObjectMapper objectMapper;

    public FileSettingsInitializer(
            @Value("${yacl.app.root:${user.home}/.yacl}") String appRoot,
            ObjectMapper objectMapper) {
        this.configDir = Path.of(appRoot).resolve("config");
        this.objectMapper = objectMapper;
    }

    @Override
    public void initializeSettings() {
        Path settingsFile = configDir.resolve("user-settings.json");

        try {
            Files.createDirectories(configDir);
            if (Files.exists(settingsFile)) {
                Map<String, Object> existing = objectMapper.readValue(
                        settingsFile.toFile(),
                        new TypeReference<Map<String, Object>>() {
                        });
                log.info("startup.phase=settings-ready source=existing keys={}", existing.size());
                return;
            }

            Map<String, Object> defaults = new HashMap<>();
            defaults.put("enableCataclysmDb", true);
            defaults.put("debugMode", false);

            objectMapper.writerWithDefaultPrettyPrinter().writeValue(settingsFile.toFile(), defaults);
            log.info("startup.phase=settings-ready source=defaults path={}", settingsFile);
        } catch (Exception ex) {
            throw new IllegalStateException("Failed to initialize baseline settings", ex);
        }
    }
}
