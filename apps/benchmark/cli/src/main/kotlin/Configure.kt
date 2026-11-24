import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

// ProbeKt cannot replace this: its --reuse compares a capture against the host JVM's runtime,
// so a device capture is rejected. Configuration here is file-to-file.
fun main(arguments: Array<String>) = command(arguments,
    "configure <probe_*.yaml> <trial_*.yaml> <configuration output directory> [<${FileNames.GLOBAL}>] [--facts=<facts.yaml>]",
    { it.count { argument -> !argument.startsWith("--") } >= 3 }) {
    val paths = arguments.filterNot { it.startsWith("--") }
    val captureFile = File(paths[0])
    val trialFile = File(paths[1])
    val configurationDirectory = File(paths[2])
    val globalFile = paths.getOrNull(3)?.let { File(it) }
    val factsFile = arguments.firstOrNull { it.startsWith("--facts=") }?.removePrefix("--facts=")?.let { File(it) }
    for (required in listOf(captureFile, trialFile)) require(required.isFile) { "missing_file: ${required.path}" }
    val configuration = Configuration(configurationDirectory.apply { mkdirs() })
    val inventoryFile = configuration.inventory(captureFile, trialFile)
    println(inventoryFile)
    if (globalFile == null) {
        System.err.println("warning: no ${FileNames.GLOBAL} given; ${FileNames.EFFECTIVE} not written")
        return@command
    }
    val effectiveFile = configuration.effective(globalFile, inventoryFile, factsFile, notes = emptyList())
    println(effectiveFile)
    val effective = configuration.readEffective(effectiveFile)
    effective.warnings.forEach { System.err.println("warning: $it") }
    effective.skipped.forEach { System.err.println("skipped: $it") }
}
