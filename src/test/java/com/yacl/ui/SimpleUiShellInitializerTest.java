package com.yacl.ui;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.yacl.bootstrap.LifecycleSnapshot;
import com.yacl.bootstrap.LifecycleState;
import com.yacl.bootstrap.LifecycleStatusProvider;
import com.yacl.ui.shell.UiDialogPresenter;
import com.yacl.ui.shell.UiDialogRequest;
import com.yacl.ui.shell.UiShellViewModelFactory;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class SimpleUiShellInitializerTest {

    @Test
    void initializeUiShellPresentsPhaseOneDialogScaffolding() {
        LifecycleStatusProvider lifecycle = () -> new LifecycleSnapshot(LifecycleState.READY, false, "READY",
                Instant.parse("2026-01-01T00:00:00Z"));
        UiShellViewModelFactory factory = new UiShellViewModelFactory(lifecycle);

        List<UiDialogRequest> presented = new ArrayList<>();
        UiDialogPresenter presenter = presented::add;

        SimpleUiShellInitializer initializer = new SimpleUiShellInitializer(factory, presenter);
        initializer.initializeUiShell();

        assertEquals(2, presented.size());
        assertEquals("ASSET_SELECTION", presented.get(0).dialogId().name());
        assertEquals("INSTALL_PROGRESS", presented.get(1).dialogId().name());
    }
}
