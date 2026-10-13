package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.File
import java.security.Security

// Run this class alone (am instrument -e class ...DeviceProbe): CryptoBenchmark builds its plan
// at class load and fails until effective.yaml exists.
class DeviceProbe {

    private val directory: File
        get() = File(
            InstrumentationRegistry.getInstrumentation().targetContext.getExternalFilesDir(null),
            "cryptobench",
        )

    @Test
    fun writesThisDevicesCaptureAndTrial() {
        val into = directory.apply { mkdirs() }
        val providers = Security.getProviders()
        val discovery = Discovery(ProbeDirectory(into))

        val probe = discovery.probe(providers)
        val trialFile = discovery.trial(probe.capture, providers)

        println("providers=" + providers.size)
        println("services=" + probe.capture.providers.sumOf { it.services.size })
        println("wrote=" + probe.captureFile.path)
        println("wrote=" + probe.classesFile.path)
        println("wrote=" + trialFile.path)
        assertTrue("no provider registered on this device", providers.isNotEmpty())
        assertTrue("capture was not written: " + probe.captureFile.path, probe.captureFile.isFile)
        assertTrue("trial was not written: " + trialFile.path, trialFile.isFile)
    }
}
