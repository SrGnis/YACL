package com.yacl.ui.shell;

import com.yacl.lifecycle.LifecycleSnapshot;
import com.yacl.lifecycle.LifecycleStatusProvider;
import java.util.List;
import org.springframework.stereotype.Component;

@Component
public class UiShellViewModelFactory {

    private final LifecycleStatusProvider lifecycleStatusProvider;

    public UiShellViewModelFactory(LifecycleStatusProvider lifecycleStatusProvider) {
        this.lifecycleStatusProvider = lifecycleStatusProvider;
    }

    public UiShellViewModel createShellModel() {
        LifecycleSnapshot snapshot = lifecycleStatusProvider.currentSnapshot();
        String status = snapshot.detail() + (snapshot.degradedMode() ? " [DEGRADED]" : "");

        return new UiShellViewModel(
                "YACL Launcher",
                status,
                snapshot,
                List.of(
                        new UiShellTabSpec(UiShellTabId.GAME, "Game", true),
                        new UiShellTabSpec(UiShellTabId.SETTINGS, "Settings", false),
                        new UiShellTabSpec(UiShellTabId.BACKUP, "Backup", false)));
    }
}
