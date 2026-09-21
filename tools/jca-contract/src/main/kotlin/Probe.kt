import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import java.io.File
import java.security.Security
import kotlin.system.exitProcess

/** probe <discovery dir> [<configuration dir>] [<global.yaml>] — the configuration dir defaults to a sibling of the discovery dir. */
fun main(arguments: Array<String>) {
    val discoveryDirectory = arguments.getOrNull(0)?.let { File(it) } ?: run {
        System.err.println("usage: probe <discovery output directory> [<configuration output directory>] [<global.yaml>]")
        exitProcess(2)
    }
    val configurationDirectory = arguments.getOrNull(1)?.let { File(it) } ?: File(discoveryDirectory.absoluteFile.parentFile, "configuration")
    val globalFile = arguments.getOrNull(2)?.let { File(it) } ?: committedGlobal()

    val discovery = Discovery(ProbeDirectory(discoveryDirectory))
    val run = discovery.probe(Security.getProviders())
    val trialFile = discovery.trial(run.capture, Security.getProviders())
    val configuration = Configuration(configurationDirectory)
    val inventoryFile = configuration.inventory(run.captureFile, trialFile)

    println(run.captureFile)
    println(run.classesFile)
    println(trialFile)
    println(inventoryFile)
    if (globalFile == null) {
        System.err.println("no config/global.yaml found; effective.yaml not written")
        return
    }
    val effectiveFile = configuration.effective(globalFile, inventoryFile)
    println(effectiveFile)
    configuration.readEffective(effectiveFile).skipped.forEach { System.err.println("skipped: $it") }
}

private fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "config/global.yaml") }.firstOrNull { it.exists() }
