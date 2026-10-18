import io.github.junekim0007.cryptobench.config.Configuration
import java.io.File
import java.io.IOException
import kotlin.system.exitProcess

// ProbeKt cannot replace this: its --reuse compares a capture against the host JVM's runtime,
// so a device capture is rejected. Configuration here is file-to-file.
fun main(arguments: Array<String>) {
    val paths = arguments.filterNot { it.startsWith("--") }
    if (paths.size < 3) {
        System.err.println("usage: configure <probe_*.yaml> <trial_*.yaml> <configuration output directory> [<global.yaml>] [--facts=<facts.yaml>]")
        exitProcess(2)
    }
    val captureFile = File(paths[0])
    val trialFile = File(paths[1])
    val configurationDirectory = File(paths[2])
    val globalFile = paths.getOrNull(3)?.let { File(it) } ?: committedGlobal()
    val factsFile = arguments.firstOrNull { it.startsWith("--facts=") }?.removePrefix("--facts=")?.let { File(it) }
    for (required in listOf(captureFile, trialFile)) {
        if (!required.isFile) {
            System.err.println("error: missing_file: ${required.path}")
            exitProcess(1)
        }
    }
    try {
        val configuration = Configuration(configurationDirectory.apply { mkdirs() })
        val inventoryFile = configuration.inventory(captureFile, trialFile)
        println(inventoryFile)
        if (globalFile == null) {
            System.err.println("warning: no config/global.yaml found; effective.yaml not written")
            return
        }
        val effectiveFile = configuration.effective(globalFile, inventoryFile, factsFile)
        println(effectiveFile)
        val effective = configuration.readEffective(effectiveFile)
        effective.warnings.forEach { System.err.println("warning: $it") }
        effective.skipped.forEach { System.err.println("skipped: $it") }
    } catch (expected: IllegalArgumentException) {
        fail(expected)
    } catch (expected: IllegalStateException) {
        fail(expected)
    } catch (expected: IOException) {
        fail(expected)
    }
}

private fun fail(error: Exception): Nothing {
    System.err.println("error: ${error.message}")
    exitProcess(1)
}

private fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "config/global.yaml") }.firstOrNull { it.exists() }
