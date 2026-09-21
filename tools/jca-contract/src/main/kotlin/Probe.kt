import io.github.junekim0007.cryptobench.config.Configuration
import io.github.junekim0007.cryptobench.config.write.ConfigFile
import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import java.io.File
import java.security.Security
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    val discoveryDirectory = arguments.getOrNull(0)?.let { File(it) } ?: run {
        System.err.println("usage: probe <discovery output directory> [<configuration output directory>]")
        exitProcess(2)
    }
    val configurationDirectory = arguments.getOrNull(1)?.let { File(it) } ?: File(discoveryDirectory.absoluteFile.parentFile, "configuration")
    val discovery = Discovery(ProbeDirectory(discoveryDirectory))
    val run = discovery.probe(Security.getProviders())
    val trialFile = discovery.trial(run.capture, Security.getProviders())
    val configFile = Configuration(ConfigFile(configurationDirectory)).generate(run.captureFile, trialFile)
    println(run.captureFile)
    println(run.classesFile)
    println(trialFile)
    println(configFile)
}
