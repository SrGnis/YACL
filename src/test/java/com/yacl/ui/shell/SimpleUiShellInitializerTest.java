package com.yacl.ui.shell;

import static org.junit.jupiter.api.Assertions.assertEquals;

import com.yacl.lifecycle.LifecycleSnapshot;
import com.yacl.lifecycle.LifecycleState;
import com.yacl.lifecycle.LifecycleStatusProvider;
import com.yacl.ui.dialog.UiDialogPresenter;
import com.yacl.ui.dialog.UiDialogRequest;
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
