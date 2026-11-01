import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.interop.InteropRun
import java.io.File

fun main(arguments: Array<String>) {
    require(arguments.size == 4) { "usage: <capture> <trial> <interop_plan.yaml> <interop.yaml>" }
    val (capture, trial, plan, out) = arguments.map(::File)
    InteropRun.run(DiscoveryCapability(capture, trial), plan, capture, out)
    println(out.path)
}
