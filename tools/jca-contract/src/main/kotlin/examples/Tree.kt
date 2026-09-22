package examples

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import java.security.Security

private val BENCHMARKED_TYPES = listOf(
    "Cipher", "MessageDigest", "Mac", "Signature",
    "KeyGenerator", "KeyPairGenerator", "KeyAgreement",
)

/** Renders CaptureQuery.tree() as the markdown in modules/environment/discovery/docs/tree.md; engine types as arguments, the benchmarked ones by default. */
fun main(arguments: Array<String>) {
    val types = arguments.toList().ifEmpty { BENCHMARKED_TYPES }
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
