package com.yacl.bootstrap;

/**
 * Minimal lifecycle query contract for UI shell consumption.
 */
public interface LifecycleStatusProvider {

    LifecycleSnapshot currentSnapshot();
}
