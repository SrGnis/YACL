package com.yacl.ui;

import com.yacl.bootstrap.UiShellInitializer;
import com.yacl.ui.shell.UiDialogId;
import com.yacl.ui.shell.UiDialogPresenter;
import com.yacl.ui.shell.UiDialogRequest;
import com.yacl.ui.shell.UiShellTabSpec;
import com.yacl.ui.shell.UiShellViewModel;
import com.yacl.ui.shell.UiShellViewModelFactory;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class SimpleUiShellInitializer implements UiShellInitializer {

    private static final Logger log = LoggerFactory.getLogger(SimpleUiShellInitializer.class);
    private final UiShellViewModelFactory shellViewModelFactory;
    private final UiDialogPresenter dialogPresenter;

    public SimpleUiShellInitializer(UiShellViewModelFactory shellViewModelFactory, UiDialogPresenter dialogPresenter) {
        this.shellViewModelFactory = shellViewModelFactory;
        this.dialogPresenter = dialogPresenter;
    }

    @Override
    public void initializeUiShell() {
        UiShellViewModel shellModel = shellViewModelFactory.createShellModel();

        String tabSummary = shellModel.tabs().stream()
                .map(UiShellTabSpec::id)
                .map(Enum::name)
                .toList()
                .toString();

        log.info(
                "ui-shell.init title={} status={} lifecycleState={} tabs={}",
                shellModel.title(),
                shellModel.statusText(),
                shellModel.lifecycle().state(),
                tabSummary);

        dialogPresenter.present(new UiDialogRequest(
                UiDialogId.ASSET_SELECTION,
                "Asset Selection",
                Map.of("phase", "scaffold", "trigger", "startup")));
        dialogPresenter.present(new UiDialogRequest(
                UiDialogId.INSTALL_PROGRESS,
                "Install Progress",
                Map.of("phase", "scaffold", "trigger", "startup")));
    }
}
