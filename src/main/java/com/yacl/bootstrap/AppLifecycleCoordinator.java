package com.yacl.bootstrap;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class AppLifecycleCoordinator implements LifecycleStatusProvider {

    private static final Logger log = LoggerFactory.getLogger(AppLifecycleCoordinator.class);

    private final PathReadinessInitializer pathInitializer;
    private final SettingsInitializer settingsInitializer;
    private final UiShellInitializer uiShellInitializer;
    private final OptionalConnectivityChecker connectivityChecker;

    private final AtomicReference<LifecycleSnapshot> snapshot;

    public AppLifecycleCoordinator(
            PathReadinessInitializer pathInitializer,
            SettingsInitializer settingsInitializer,
            UiShellInitializer uiShellInitializer,
            OptionalConnectivityChecker connectivityChecker) {
        this.pathInitializer = pathInitializer;
        this.settingsInitializer = settingsInitializer;
        this.uiShellInitializer = uiShellInitializer;
        this.connectivityChecker = connectivityChecker;
        this.snapshot = new AtomicReference<>(
                new LifecycleSnapshot(LifecycleState.BOOTING, false, "Boot sequence not started", Instant.now()));
    }

    public synchronized void startup() {
        setSnapshot(LifecycleState.BOOTING, false, "Boot sequence started");
        log.info("startup.phase=booting");

        pathInitializer.initializePaths();
        log.info("startup.phase=paths-complete");

        settingsInitializer.initializeSettings();
        log.info("startup.phase=settings-complete");

        uiShellInitializer.initializeUiShell();
        log.info("startup.phase=ui-shell-complete");

        ConnectivityStatus connectivity = connectivityChecker.check();
        if (connectivity == ConnectivityStatus.UNAVAILABLE) {
            setSnapshot(LifecycleState.READY, true, "READY (degraded: optional connectivity unavailable)");
            log.warn("startup.phase=ready mode=degraded reason=optional-connectivity-unavailable");
            return;
        }

        setSnapshot(LifecycleState.READY, false, "READY");
        log.info("startup.phase=ready mode=normal");
    }

    public synchronized void initiateShutdown() {
        LifecycleSnapshot current = snapshot.get();
        if (current.state() == LifecycleState.SHUTTING_DOWN) {
            return;
        }

        setSnapshot(LifecycleState.SHUTTING_DOWN, current.degradedMode(), "Shutdown requested");
        log.info("lifecycle.phase=shutting-down");
    }

    @Override
    public LifecycleSnapshot currentSnapshot() {
        return snapshot.get();
    }

    private void setSnapshot(LifecycleState state, boolean degraded, String detail) {
        snapshot.set(new LifecycleSnapshot(state, degraded, detail, Instant.now()));
    }
}
