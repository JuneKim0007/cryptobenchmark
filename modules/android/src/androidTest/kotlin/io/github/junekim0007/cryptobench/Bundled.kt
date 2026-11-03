package io.github.junekim0007.cryptobench

import androidx.test.platform.app.InstrumentationRegistry
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import java.io.File

/** Installs the bundledProviders of a pushed effective.yaml into this process; every class that calls a provider does this first. */
object Bundled {

    fun installFrom(effective: File) {
        val bundled = BundledProviders.read(YamlCodec().load(effective.readText()))
        BundledInstaller(ProviderFactory(InstrumentationRegistry.getInstrumentation().targetContext.classLoader)).install(bundled)
    }
}
