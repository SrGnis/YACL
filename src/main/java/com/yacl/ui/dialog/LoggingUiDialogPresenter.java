package com.yacl.ui.dialog;

import java.util.Objects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;

@Component
public class LoggingUiDialogPresenter implements UiDialogPresenter {

    private static final Logger log = LoggerFactory.getLogger(LoggingUiDialogPresenter.class);

    @Override
    public void present(UiDialogRequest request) {
        Objects.requireNonNull(request, "request must not be null");
        log.info("ui-shell.dialog.open id={} title={} payloadKeys={}",
                request.dialogId(),
                request.title(),
                request.payload().size());
    }
}
