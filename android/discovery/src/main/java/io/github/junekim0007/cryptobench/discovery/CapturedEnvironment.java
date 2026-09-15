package io.github.junekim0007.cryptobench.discovery;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** What the JCA looked like on one device at one moment. Serialises as-is; holds no logic. */
public final class CapturedEnvironment {

    public static final int SCHEMA_VERSION = 1;

    private final int schemaVersion;
    private final long capturedAtMillis;
    private final RuntimeInfo runtime;
    private final List<ProviderEntry> providers;

    public CapturedEnvironment(int schemaVersion, long capturedAtMillis,
                               RuntimeInfo runtime, List<ProviderEntry> providers) {
        if (runtime == null) {
            throw new NullPointerException("runtime");
        }
        this.schemaVersion = schemaVersion;
        this.capturedAtMillis = capturedAtMillis;
        this.runtime = runtime;
        this.providers = providers == null
                ? Collections.<ProviderEntry>emptyList()
                : Collections.unmodifiableList(new ArrayList<ProviderEntry>(providers));
    }

    public int getSchemaVersion() {
        return schemaVersion;
    }

    public long getCapturedAtMillis() {
        return capturedAtMillis;
    }

    public RuntimeInfo getRuntime() {
        return runtime;
    }

    public List<ProviderEntry> getProviders() {
        return providers;
    }
}
