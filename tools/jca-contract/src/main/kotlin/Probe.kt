import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import java.io.File
import java.io.IOException
import java.security.Security
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    val paths = arguments.filterNot { it.startsWith("--") }
    val reuse = arguments.contains("--reuse")
    val discoveryDirectory = paths.getOrNull(0)?.let { File(it) } ?: run {
        System.err.println("usage: probe <discovery output directory> [<configuration output directory>] [<global.yaml>] [--reuse]")
        exitProcess(2)
    }
    val configurationDirectory = paths.getOrNull(1)?.let { File(it) } ?: File(discoveryDirectory.absoluteFile.parentFile, "configuration")
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
    val reused = if (reuse) discovery.reusable() else null
    val captureFile: File
    val classesFile: File
    val trialFile: File
    if (reused != null) {
        captureFile = reused.captureFile
        classesFile = reused.classesFile
        trialFile = reused.trialFile
        System.err.println("reused: ${reused.captureFile.name}")
    } else {
        val probe = discovery.probe(Security.getProviders())
        captureFile = probe.captureFile
        classesFile = probe.classesFile
        trialFile = discovery.trial(probe.capture, Security.getProviders())
    }
    val configuration = Configuration(configurationDirectory)
    val inventoryFile = configuration.inventory(captureFile, trialFile)
    println(captureFile)
    println(classesFile)
    println(trialFile)
    println(inventoryFile)
    if (globalFile == null) {
        System.err.println("warning: no config/global.yaml found; effective.yaml not written")
        return
    }
    val effectiveFile = configuration.effective(globalFile, inventoryFile)
    println(effectiveFile)
    val effective = configuration.readEffective(effectiveFile)
    effective.warnings.forEach { System.err.println("warning: $it") }
    effective.skipped.forEach { System.err.println("skipped: $it") }
}

private fun fail(error: Exception): Nothing {
    System.err.println("error: ${error.message}")
    exitProcess(1)
}

private fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "config/global.yaml") }.firstOrNull { it.exists() }
