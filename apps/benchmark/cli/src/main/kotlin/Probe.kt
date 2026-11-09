import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.files.Beside
import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.files.Folders
import java.io.File
import java.io.IOException
import java.security.Security
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    val paths = arguments.filterNot { it.startsWith("--") }
    val reuse = arguments.contains("--reuse")
    val discoveryDirectory = paths.getOrNull(0)?.let { File(it) } ?: run {
        System.err.println("usage: probe <discovery output directory> [<configuration output directory>] [<${FileNames.GLOBAL}>] [--reuse]")
        exitProcess(2)
    }
    val configurationDirectory = paths.getOrNull(1)?.let { File(it) } ?: Beside.file(discoveryDirectory, Folders.CONFIGURATION)
    val globalFile = paths.getOrNull(2)?.let { File(it) } ?: committedGlobal()
    try {
        run(discoveryDirectory, configurationDirectory, globalFile, reuse)
    } catch (expected: IllegalArgumentException) {
        fail(expected)
    } catch (expected: IllegalStateException) {
        fail(expected)
    } catch (expected: IOException) {
        fail(expected)
    }
}

private fun run(discoveryDirectory: File, configurationDirectory: File, globalFile: File?, reuse: Boolean) {
    val discovery = Discovery(ProbeDirectory(discoveryDirectory))
    val installed = globalFile?.let(HostBundled::fromGlobal).orEmpty()
    val reused = if (reuse) discovery.reusable() else null
    val captureFile: File
    val trialFile: File
    val requirementsFile: File
    if (reused != null) {
        captureFile = reused.captureFile
        trialFile = reused.trialFile
        requirementsFile = reused.requirementsFile
        System.err.println("reused: ${reused.captureFile.name}")
    } else {
        val probe = discovery.probe(Security.getProviders(), bundled = installed)
        captureFile = probe.captureFile
        val files = discovery.trial(probe.capture, Security.getProviders())
        trialFile = files.trialFile
        requirementsFile = files.requirementsFile
    }
    val configuration = Configuration(configurationDirectory)
    val inventoryFile = configuration.inventory(captureFile, trialFile)
    println(captureFile)
    println(trialFile)
    println(requirementsFile)
    println(inventoryFile)
    if (globalFile == null) {
        System.err.println("warning: no ${Folders.CONFIG}/${FileNames.GLOBAL} found; ${FileNames.EFFECTIVE} not written")
        return
    }
    val effectiveFile = configuration.effective(globalFile, inventoryFile)
    println(effectiveFile)
    val effective = configuration.readEffective(effectiveFile)
    effective.warnings.forEach { System.err.println("warning: $it") }
    effective.skipped.forEach { System.err.println("skipped: $it") }
}
