package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.jca.failure.Attempt

/** Calls each variant once and runs the scope's interop check. */
object ScopeCheck {

    const val PASSED = "passed"
    const val UNCHECKED = "unchecked"
    const val INTEROP_FAILED = "interop_failed"
    const val CALL_FAILED = "call_failed"
    const val NOT_COMPARABLE = "not_comparable"

    data class Verdict(val id: String, val interop: String, val check: String, val reason: String?)

    fun of(scope: Scope): Verdict {
        val check = when (scope.interop) {
            ScopeInterop.SameOutput -> "same_output"
            is ScopeInterop.RoundTrip -> "round_trip"
            is ScopeInterop.Unchecked -> "none"
        }
        val verdict = { interop: String, reason: String? -> Verdict(scope.id, interop, check, reason) }
        val before = Attempt.of { scope.before() }.getOrElse { return verdict(CALL_FAILED, "before: ${describe(it)}") }
        val after = Attempt.of { scope.after() }.getOrElse { return verdict(CALL_FAILED, "after: ${describe(it)}") }
        return when (val interop = scope.interop) {
            is ScopeInterop.Unchecked -> verdict(UNCHECKED, interop.reason)
            ScopeInterop.SameOutput -> sameOutput(scope, before, after, verdict)
            is ScopeInterop.RoundTrip -> roundTrip(interop, verdict)
        }
    }

    private fun sameOutput(scope: Scope, before: Any?, after: Any?, verdict: (String, String?) -> Verdict): Verdict {
        if (before == null || before == Unit) return verdict(UNCHECKED, "no_output: before returned nothing to compare")
        if (!comparable(before)) return verdict(NOT_COMPARABLE, "identity_only_output: ${before.javaClass.name} has no value equality")
        val again = Attempt.of { scope.before() }.getOrElse { return verdict(CALL_FAILED, "before: ${describe(it)}") }
        if (!same(before, again)) return verdict(UNCHECKED, "nondeterministic_output: two calls of before differ on one input")
        if (!same(before, after)) return verdict(INTEROP_FAILED, "outputs_differ: before and after differ on one input")
        return verdict(PASSED, null)
    }

    private fun roundTrip(interop: ScopeInterop.RoundTrip, verdict: (String, String?) -> Verdict): Verdict {
        val directions = listOf(
            "before_to_after" to { interop.consumeAfter(interop.produceBefore()) },
            "after_to_before" to { interop.consumeBefore(interop.produceAfter()) },
        )
        for ((direction, restore) in directions) {
            val restored = Attempt.of(restore).getOrElse { return verdict(INTEROP_FAILED, "$direction: ${describe(it)}") }
            if (!same(restored, interop.expected)) return verdict(INTEROP_FAILED, "$direction: restored value differs from the input")
        }
        return verdict(PASSED, null)
    }

    // identity equality would read every two calls as different: a false nondeterministic_output
    fun comparable(value: Any): Boolean = when {
        value is ByteArray || value is CharArray || value is Array<*> -> true
        value.javaClass.isArray -> false
        else -> value.javaClass.getMethod("equals", Any::class.java).declaringClass != Any::class.java
    }

    fun same(a: Any?, b: Any?): Boolean = when {
        a is ByteArray && b is ByteArray -> a.contentEquals(b)
        a is CharArray && b is CharArray -> a.contentEquals(b)
        a is Array<*> && b is Array<*> -> a.contentDeepEquals(b)
        else -> a == b
    }

    private fun describe(failure: Throwable): String = "${failure.javaClass.simpleName}: ${failure.message}"
}
