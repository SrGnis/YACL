package com.yacl.bootstrap;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class ConfigurableConnectivityChecker implements OptionalConnectivityChecker {

    private final boolean simulateOffline;

    public ConfigurableConnectivityChecker(
            @Value("${yacl.startup.simulate-offline:false}") boolean simulateOffline) {
        this.simulateOffline = simulateOffline;
    }

    @Override
    public ConnectivityStatus check() {
        return simulateOffline ? ConnectivityStatus.UNAVAILABLE : ConnectivityStatus.AVAILABLE;
    }
}
