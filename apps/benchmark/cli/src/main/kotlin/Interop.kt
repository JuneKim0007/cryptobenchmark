import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
import java.io.File

fun main(arguments: Array<String>) = command(arguments, "<capture> <trial> <${FileNames.EFFECTIVE}> <${FileNames.INTEROP_PLAN}> <${FileNames.INTEROP_RESULT}>", { it.size == 5 }) {
    val (capture, trial, effective, plan, out) = arguments.map(::File)
    HostBundled.fromEffective(effective)
    InteropRun.run(DiscoveryCapability(capture, trial), plan, capture, out)
    println(out.path)
}
