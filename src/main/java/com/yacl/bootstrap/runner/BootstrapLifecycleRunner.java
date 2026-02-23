package com.yacl.bootstrap.runner;

import com.yacl.lifecycle.AppLifecycleCoordinator;
import jakarta.annotation.PreDestroy;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

@Component
public class BootstrapLifecycleRunner implements ApplicationRunner {

    private final AppLifecycleCoordinator lifecycleCoordinator;

    public BootstrapLifecycleRunner(AppLifecycleCoordinator lifecycleCoordinator) {
        this.lifecycleCoordinator = lifecycleCoordinator;
    }

    @Override
    public void run(ApplicationArguments args) {
        lifecycleCoordinator.startup();
    }

    @PreDestroy
    public void onShutdown() {
        lifecycleCoordinator.initiateShutdown();
    }
}
