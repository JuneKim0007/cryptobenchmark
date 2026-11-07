import io.github.junekim0007.cryptobench.config.AuthoredFiles
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.discovery.bundled.InstalledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import java.io.File

// The host's providers.bundled, as Bundled.kt does on a device: the artifacts are on this JVM's classpath by -PbundledArtifacts.
internal object HostBundled {

    fun fromGlobal(global: File): List<InstalledProvider> =
        install(AuthoredFiles().read(global).global.providers.bundled.map { BundledProvider(it.artifact, it.create, it.alias) })

    fun fromEffective(effective: File): List<InstalledProvider> = install(BundledProviders.read(YamlCodec().load(effective.readText())))

    private fun install(bundled: List<BundledProvider>): List<InstalledProvider> =
        BundledInstaller(ProviderFactory(HostBundled::class.java.classLoader)).install(bundled)
}
