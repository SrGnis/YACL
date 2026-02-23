package com.yacl.lifecycle;

/**
 * Minimal lifecycle query contract for UI shell consumption.
 */
public interface LifecycleStatusProvider {

    LifecycleSnapshot currentSnapshot();
}
