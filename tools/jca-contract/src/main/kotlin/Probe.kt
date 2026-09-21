import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import java.io.File
import java.io.IOException
import java.security.Security
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    val discoveryDirectory = arguments.getOrNull(0)?.let { File(it) } ?: run {
        System.err.println("usage: probe <discovery output directory> [<configuration output directory>] [<global.yaml>]")
        exitProcess(2)
    }
    val configurationDirectory = arguments.getOrNull(1)?.let { File(it) } ?: File(discoveryDirectory.absoluteFile.parentFile, "configuration")
    val globalFile = arguments.getOrNull(2)?.let { File(it) } ?: committedGlobal()
    try {
        run(discoveryDirectory, configurationDirectory, globalFile)
    } catch (expected: IllegalArgumentException) {
        fail(expected)
    } catch (expected: IllegalStateException) {
        fail(expected)
    } catch (expected: IOException) {
        fail(expected)
    }
}

private fun run(discoveryDirectory: File, configurationDirectory: File, globalFile: File?) {
    val discovery = Discovery(ProbeDirectory(discoveryDirectory))
    val probe = discovery.probe(Security.getProviders())
    val trialFile = discovery.trial(probe.capture, Security.getProviders())
    val configuration = Configuration(configurationDirectory)
    val inventoryFile = configuration.inventory(probe.captureFile, trialFile)
    println(probe.captureFile)
    println(probe.classesFile)
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
