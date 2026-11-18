package io.github.junekim0007.cryptobench.discovery.trial.keystore

import java.security.Provider

/** One key of a keystore trial row: what the generator is asked for. curve set: the curve instead of the block's own. */
internal data class KeystoreRequest(val type: String, val algorithm: String, val authorizations: Map<String, Any>, val backing: String, val keySize: Int? = null, val curve: String = "")

/** What the keystore trial needs of a runtime: the reflective one on a device, a fake in tests. */
internal interface KeystoreMaker {

    /** Null when the runtime has the keystore classes; else the not_supported reason the section is absent with. */
    fun missing(): String?

    /** Whether the device declares StrongBox; null when it cannot be read. */
    fun strongBox(): Boolean?

    fun generate(provider: Provider, request: KeystoreRequest, alias: String, sdkInt: Int)

    /** Deletes the provider's aliases that start with the prefix. */
    fun sweep(provider: Provider, prefix: String)

    fun delete(provider: Provider, alias: String)

    /** A builder member this API level lacks. */
    class AbsentMember(reason: String) : UnsupportedOperationException(reason)
}
