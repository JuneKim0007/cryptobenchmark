package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.files.FileNames
import org.junit.Test
import java.io.File

// Run alone (am instrument -e class ...ScopedInterop) after pushing effective.yaml: one process checks every scope.
class ScopedInterop {

    @Test
    fun checksEveryScope() {
        val effective = File(DevicePlan.directory, FileNames.EFFECTIVE)
        check(effective.isFile) { "missing_file: ${effective.absolutePath}, push ${FileNames.EFFECTIVE} first" }
        Bundled.installFrom(effective)
        ScopeInteropFile.write(DevicePlan.directory, ScopeCatalog.load().map(ScopeCheck::of))
    }
}
