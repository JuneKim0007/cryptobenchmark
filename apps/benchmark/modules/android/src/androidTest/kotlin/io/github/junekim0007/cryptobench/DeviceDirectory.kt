package io.github.junekim0007.cryptobench

import android.os.Build
import androidx.test.platform.app.InstrumentationRegistry
import java.io.File

// adb shell cannot read Android/data on API 30, so from API 29 (androidx's own output rule) use the media directory.
// Paired with apps/benchmark-runner/device/adb.py directories.
internal object DeviceDirectory {

    const val NAME = "cryptobench"

    @Suppress("DEPRECATION")
    val plan: File
        get() {
            val context = InstrumentationRegistry.getInstrumentation().targetContext
            val parent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) context.externalMediaDirs.firstOrNull() else context.getExternalFilesDir(null)
            return File(checkNotNull(parent) { "no_storage: external storage is not mounted for ${context.packageName}" }, NAME)
        }
}
