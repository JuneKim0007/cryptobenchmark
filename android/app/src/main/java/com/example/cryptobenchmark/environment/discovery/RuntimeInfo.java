package com.example.cryptobenchmark.environment.discovery;

/**
 * Provenance for one capture. Held as plain strings so {@link ProviderProbe} stays free of
 * android.* and can run on a desktop JVM; {@link #ofDevice()} is the only Android-aware part.
 */
public final class RuntimeInfo {

    private final String model;
    private final String manufacturer;
    private final String hardware;
    private final int sdkInt;
    private final String release;
    private final String javaVersion;

    public RuntimeInfo(String model, String manufacturer, String hardware,
                       int sdkInt, String release, String javaVersion) {
        this.model = model == null ? "" : model;
        this.manufacturer = manufacturer == null ? "" : manufacturer;
        this.hardware = hardware == null ? "" : hardware;
        this.sdkInt = sdkInt;
        this.release = release == null ? "" : release;
        this.javaVersion = javaVersion == null ? "" : javaVersion;
    }

    /** Reads android.os.Build reflectively so this class still loads in a plain JVM test. */
    public static RuntimeInfo ofDevice() {
        return new RuntimeInfo(
                buildField("MODEL"),
                buildField("MANUFACTURER"),
                buildField("HARDWARE"),
                buildVersionSdkInt(),
                buildVersionField("RELEASE"),
                System.getProperty("java.version"));
    }

    public static RuntimeInfo unknown() {
        return new RuntimeInfo("", "", "", 0, "", System.getProperty("java.version"));
    }

    private static String buildField(String name) {
        try {
            return String.valueOf(Class.forName("android.os.Build").getField(name).get(null));
        } catch (Exception e) {
            return "";
        }
    }

    private static String buildVersionField(String name) {
        try {
            return String.valueOf(Class.forName("android.os.Build$VERSION").getField(name).get(null));
        } catch (Exception e) {
            return "";
        }
    }

    private static int buildVersionSdkInt() {
        try {
            Object value = Class.forName("android.os.Build$VERSION").getField("SDK_INT").get(null);
            return value instanceof Integer ? ((Integer) value).intValue() : 0;
        } catch (Exception e) {
            return 0;
        }
    }

    public String getModel() {
        return model;
    }

    public String getManufacturer() {
        return manufacturer;
    }

    public String getHardware() {
        return hardware;
    }

    public int getSdkInt() {
        return sdkInt;
    }

    public String getRelease() {
        return release;
    }

    public String getJavaVersion() {
        return javaVersion;
    }
}
