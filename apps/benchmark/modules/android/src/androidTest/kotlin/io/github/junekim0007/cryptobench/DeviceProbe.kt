package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

// Run this class alone (am instrument -e class ...DeviceProbe): CryptoBenchmark builds its plan
// at class load and fails until effective.yaml exists.
class DeviceProbe {

    @Test
    fun writesThisDevicesCaptureAndTrial() {
        val into = DeviceDirectory.plan.apply { mkdirs() }
        val instrumentation = InstrumentationRegistry.getInstrumentation()
        val bundled = InstrumentationRegistry.getArguments().getString(BundledProviders.KEY)
            ?.let { BundledProviders.read(YamlCodec().load(it)) }.orEmpty()
        val installed = BundledInstaller(ProviderFactory(instrumentation.targetContext.classLoader)).install(bundled)
        val providers = Security.getProviders()
        val discovery = Discovery(ProbeDirectory(into))
        // A device clock can be months off: the host's time names the files, the device's stands beside it.
        val capturedAt = InstrumentationRegistry.getArguments().getString(HOST_MILLIS)?.toLong() ?: System.currentTimeMillis()

        val probe = discovery.probe(providers, capturedAtMillis = capturedAt, bundled = installed)
        val started = System.nanoTime()
        val files = discovery.trial(probe.capture, providers)
        val trialFile = files.trialFile
        println("trialMillis=" + (System.nanoTime() - started) / 1_000_000)

        println("providers=" + providers.size)
        probe.capture.providers.forEach { println("provider=${it.precedence}:${it.name} origin=${it.origin.key} ${it.artifact}".trimEnd()) }
        println("services=" + probe.capture.providers.sumOf { it.services.size })
        println("wrote=" + probe.captureFile.path)
        println("wrote=" + trialFile.path)
        println("wrote=" + files.requirementsFile.path)
        assertTrue("no provider registered on this device", providers.isNotEmpty())
        assertTrue("capture was not written: " + probe.captureFile.path, probe.captureFile.isFile)
        assertTrue("trial was not written: " + trialFile.path, trialFile.isFile)
        assertTrue("requirements were not written: " + files.requirementsFile.path, files.requirementsFile.isFile)
    }

    private companion object {
        const val HOST_MILLIS = "hostMillis"
    }
}
