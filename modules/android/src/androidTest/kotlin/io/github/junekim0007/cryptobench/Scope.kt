package io.github.junekim0007.cryptobench

/** One app function, original and patched, each called on the same synthesised inputs. */
class Scope(val id: String, val before: () -> Any?, val after: () -> Any?, val interop: ScopeInterop)

sealed interface ScopeInterop {

    object SameOutput : ScopeInterop

    class RoundTrip(
        val expected: Any?,
        val produceBefore: () -> Any?,
        val produceAfter: () -> Any?,
        val consumeBefore: (Any?) -> Any?,
        val consumeAfter: (Any?) -> Any?,
    ) : ScopeInterop

    class Unchecked(val reason: String) : ScopeInterop
}
