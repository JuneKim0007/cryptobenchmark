package io.github.junekim0007.cryptobench.preparation.key.secure

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.shared.FailureText
import java.security.KeyStore
import java.security.Security
import java.security.spec.AlgorithmParameterSpec
import java.util.zip.CRC32

/**
 * A secure case's key slot inside its provider: one alias per case, emptied after every call so each generation writes a free slot.
 * The provider's own KeyStore service holds the slot; aliases a killed process left behind are swept before the first spec.
 */
internal class SecureKey(private val case: BenchmarkCase, private val sdkInt: Int? = null) {

    val alias: String = PREFIX + java.lang.Long.toHexString(CRC32().apply { update(case.id.toByteArray(Charsets.UTF_8)) }.value)

    private val store: KeyStore by lazy {
        val type = Security.getProvider(case.provider)?.services?.firstOrNull { it.type == KEY_STORE }?.algorithm
            ?: throw IllegalStateException("${case.provider} registers no $KEY_STORE")
        KeyStore.getInstance(type, case.provider).apply { load(null) }
    }

    fun spec(parameterSpec: AlgorithmParameterSpec?): AlgorithmParameterSpec {
        KeystoreSpec.missing()?.let { throw KeystoreSpec.AbsentMember(it) }
        store.aliases().toList().filter { it.startsWith(PREFIX) }.forEach(store::deleteEntry)
        return KeystoreSpec.build(alias, case.keystore, case.keySize, parameterSpec, case.keySource.requestedBacking, sdkInt)
    }

    fun delete() {
        store.deleteEntry(alias)
    }

    /** The coded reason a secure step failed: StrongBox absent, a member this API lacks, else the keystore refusing this key. */
    fun refusal(failure: Throwable): String {
        if (failure is KeystoreSpec.AbsentMember) return failure.message.orEmpty()
        val chain = generateSequence(failure) { it.cause }.toList()
        if (chain.any { it.javaClass.simpleName == STRONGBOX_UNAVAILABLE }) return FailureText.of(failure, "strongbox_unavailable: ${case.provider} ${case.keySource.requestedBacking}: ")
        val size = case.keySize?.let { "/$it" }.orEmpty()
        return FailureText.of(chain.last(), "keystore_unsupported: ${case.type} ${case.algorithm}$size: ")
    }

    private companion object {
        const val PREFIX = "cryptobench-"
        const val KEY_STORE = "KeyStore"
        const val STRONGBOX_UNAVAILABLE = "StrongBoxUnavailableException"
    }
}
