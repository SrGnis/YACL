package com.yacl.ui.shell;

import java.util.Map;
import java.util.Objects;

/**
 * Dialog invocation contract for Phase 1 vertical slice wiring.
 */
public record UiDialogRequest(UiDialogId dialogId, String title, Map<String, Object> payload) {

    public UiDialogRequest {
        dialogId = Objects.requireNonNull(dialogId, "dialogId must not be null");
        title = Objects.requireNonNull(title, "title must not be null");
        payload = (payload == null) ? Map.of() : Map.copyOf(payload);
    }
}
