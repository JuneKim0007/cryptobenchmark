package io.github.junekim0007.cryptobench.discovery.contract

/**
 * Provenance for one capture. Plain strings, so this module stays free of android.* and runs on a
 * desktop JVM; [ofDevice] is the only Android-aware part.
 */
data class RuntimeInfo(
    val model: String = "",
    val manufacturer: String = "",
    val hardware: String = "",
    val sdkInt: Int = 0,
    val release: String = "",
    val javaVersion: String = systemJavaVersion(),
) {

    companion object {

        /** Reads android.os.Build reflectively so this class still loads in a plain JVM test. */
        fun ofDevice(): RuntimeInfo = RuntimeInfo(
            model = buildField("android.os.Build", "MODEL"),
            manufacturer = buildField("android.os.Build", "MANUFACTURER"),
            hardware = buildField("android.os.Build", "HARDWARE"),
            sdkInt = sdkInt(),
            release = buildField("android.os.Build\$VERSION", "RELEASE"),
        )

        fun unknown(): RuntimeInfo = RuntimeInfo()

        private fun systemJavaVersion(): String = System.getProperty("java.version") ?: ""

        private fun buildField(className: String, name: String): String = try {
            Class.forName(className).getField(name).get(null).toString()
        } catch (e: Exception) {
            ""
        }

        private fun sdkInt(): Int = try {
            Class.forName("android.os.Build\$VERSION").getField("SDK_INT").get(null) as? Int ?: 0
        } catch (e: Exception) {
            0
        }
    }
}
