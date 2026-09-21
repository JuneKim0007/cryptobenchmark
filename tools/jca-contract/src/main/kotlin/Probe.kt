import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import java.io.File
import java.security.Security
import kotlin.system.exitProcess

fun main(arguments: Array<String>) {
    val directory = arguments.firstOrNull() ?: run {
        System.err.println("usage: probe <output directory>")
        exitProcess(2)
    }
    val discovery = Discovery(ProbeDirectory(File(directory)))
    val run = discovery.probe(Security.getProviders())
    println(run.captureFile)
    println(run.classesFile)
    println(discovery.trial(run.capture, Security.getProviders()))
}
