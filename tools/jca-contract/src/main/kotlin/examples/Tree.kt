package examples

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import io.github.junekim0007.cryptobench.discovery.setting.BenchmarkScope
import java.security.Security

/** Renders CaptureQuery.tree() as the markdown in modules/environment/discovery/docs/tree.md; engine types as arguments, BenchmarkScope by default. */
fun main(arguments: Array<String>) {
    val types = arguments.toList().ifEmpty { BenchmarkScope.TYPES.toList() }
    val tree = CaptureQuery(ProviderProbe().capture(Security.getProviders())).tree()
    for ((type, algorithms) in tree) {
        if (types.none { it.equals(type, ignoreCase = true) }) continue
        println("## $type\n")
        for ((algorithm, shape) in algorithms) {
            println("### $algorithm\n")
            if (shape.modes.isNotEmpty()) println("- modes: ${shape.modes.joinToString(", ")}")
            if (shape.paddings.isNotEmpty()) println("- paddings: ${shape.paddings.joinToString(", ")}")
            println("- providers: ${shape.providers.joinToString(", ")}\n")
        }
    }
}
