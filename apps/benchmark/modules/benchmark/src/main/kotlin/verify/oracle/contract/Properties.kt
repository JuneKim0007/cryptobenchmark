package io.github.junekim0007.cryptobench.benchmark.verify.oracle.contract

import io.github.junekim0007.cryptobench.benchmark.verify.oracle.CheckedCall
import io.github.junekim0007.cryptobench.preparation.interop.report.Outcome

/** The JCA contract properties one operation's output must hold, each named with its verdict. */
fun interface Properties {
    fun of(call: CheckedCall): Map<String, Outcome>
}

internal fun holds(condition: Boolean, failure: () -> String): Outcome = if (condition) Outcome.Pass else Outcome.Fail(failure())

internal fun flipped(bytes: ByteArray, at: Int = bytes.size - 1): ByteArray = bytes.copyOf().also { it[at] = (it[at].toInt() xor 1).toByte() }
