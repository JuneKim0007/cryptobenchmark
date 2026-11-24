import io.github.junekim0007.cryptobench.config.AuthoredFiles
import io.github.junekim0007.cryptobench.contract.bundled.BundledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.BundledInstaller
import io.github.junekim0007.cryptobench.discovery.bundled.BundledProviders
import io.github.junekim0007.cryptobench.discovery.bundled.InstalledProvider
import io.github.junekim0007.cryptobench.discovery.bundled.ProviderFactory
import io.github.junekim0007.cryptobench.document.YamlCodec
import java.io.File

// The host's providers.bundled, as Bundled.kt does on a device: the artifacts are on this JVM's classpath by -PbundledArtifacts.
internal object HostBundled {

    // set by this CLI's build: the artifacts whose POM packaging is aar, kept off this JVM's classpath
    private const val ANDROID_ONLY = "bundled.androidOnly"

    data class Installed(val providers: List<InstalledProvider>, val notes: List<String>)

    fun fromGlobal(global: File): Installed = install(AuthoredFiles().read(global).global.providers.bundled)

    // configure wrote the notes into the run's report.yaml; a later step repeats them
    fun fromEffective(effective: File) =
        install(BundledProviders.read(YamlCodec.CAPTURE.load(effective.readText()))).notes.forEach { System.err.println("warning: $it") }

    fun install(bundled: List<BundledProvider>, androidOnly: Set<String> = androidOnly()): Installed {
        val (skipped, kept) = bundled.partition { it.artifact in androidOnly }
        return Installed(BundledInstaller(ProviderFactory(HostBundled::class.java.classLoader)).install(kept), skipped.map(::note))
    }

    private fun note(spec: BundledProvider): String =
        "bundled_android_only: ${spec.artifact} (${spec.alias ?: spec.create}): its POM packaging is aar, which a host JVM cannot load; not installed"

    private fun androidOnly(): Set<String> = System.getProperty(ANDROID_ONLY).orEmpty().split(',').filter { it.isNotEmpty() }.toSet()
}
