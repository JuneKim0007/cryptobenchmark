package io.github.junekim0007.cryptobench.benchmark.verify.oracle.cross

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import java.security.AlgorithmParameters
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.PSSParameterSpec
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec
import javax.crypto.spec.OAEPParameterSpec

/** The parameters the case's call used, in a form another provider takes: a spec read from the engine's report, the report itself, or the case's fixed spec. */
internal object PeerParameters {

    // Most specific first: GCM parameters may also answer as a bare IV.
    private val SPECS = listOf(GCMParameterSpec::class.java, OAEPParameterSpec::class.java, PSSParameterSpec::class.java, IvParameterSpec::class.java)

    fun portable(reported: AlgorithmParameters): Any =
        SPECS.firstNotNullOfOrNull { runCatching { reported.getParameterSpec(it) }.getOrNull() } ?: reported

    // null: the call used none. A spec drawn per call that the engine does not report cannot be recovered.
    fun used(prepared: PreparedCase, reported: AlgorithmParameters?): Any? {
        if (reported != null) return portable(reported)
        val bound = prepared.parameters ?: return null
        if (bound.varies) throw PeerRefusal("parameters_not_recoverable", "the engine reports none and the case draws them per call")
        return bound.next()
    }

    fun spec(used: Any?): AlgorithmParameterSpec? = when (used) {
        null -> null
        is AlgorithmParameterSpec -> used
        is AlgorithmParameters -> SPECS.firstNotNullOfOrNull { runCatching { used.getParameterSpec(it) }.getOrNull() }
            ?: throw PeerRefusal("parameters_not_recoverable", "no spec read from ${used.algorithm} parameters")
        else -> throw PeerRefusal("parameters_not_recoverable", "${used.javaClass.simpleName}")
    }
}
