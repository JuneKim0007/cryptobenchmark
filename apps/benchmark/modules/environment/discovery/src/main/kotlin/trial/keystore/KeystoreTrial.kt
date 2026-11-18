package io.github.junekim0007.cryptobench.discovery.trial.keystore

import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreRow
import io.github.junekim0007.cryptobench.discovery.contract.KeystoreSection
import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.ServiceKey
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.failure.ErrorText
import java.security.Provider

/**
 * One key per (generator, key size or curve, hardware path) for each generator the requirement trial found keystore-born and the catalogue gives a keystore block:
 * a fresh alias, deleted after. TEE always; StrongBox unless the device declares it has none.
 */
class KeystoreTrial internal constructor(private val maker: KeystoreMaker, private val catalogue: () -> KeystoreCatalogue) {

    constructor() : this(ReflectiveKeystore, { KeystoreCatalogue.bundled })

    fun run(capture: CapturedEnvironment, requirements: RequirementReport, providers: Array<Provider>?): KeystoreSection {
        maker.missing()?.let { return KeystoreSection(absent = it) }
        val installed = providers.orEmpty().associateBy { it.name }
        val generators = requirements.services.filter { it.reason == ServiceRequirement.KEYSTORE_BORN_KEY && it.transformationOf.isEmpty() && ServiceKey.fold(it.type) in GENERATORS }
        if (generators.isEmpty()) return KeystoreSection()
        val strongBox = maker.strongBox()
        val blocks = catalogue()
        var next = 0
        val swept = HashSet<String>()
        val rows = generators.flatMap { service ->
            val provider = installed[service.provider] ?: return@flatMap emptyList()
            val block = blocks.of(service.type, listOf(service.algorithm) + aliases(capture, service)) ?: return@flatMap emptyList()
            if (swept.add(provider.name)) Attempt.of { maker.sweep(provider, PREFIX) }
            requests(service, block).map { request ->
                if (request.backing == KeystoreRow.STRONGBOX && strongBox == false) row(provider, request, "strongbox_unavailable: ${provider.name} ${request.backing}: the device declares no $STRONGBOX_FEATURE")
                else attempt(provider, request, PREFIX + next++, capture.runtime.sdkInt)
            }
        }
        return KeystoreSection(rows)
    }

    private fun requests(service: ServiceRequirement, block: KeystoreCatalogue.Block): List<KeystoreRequest> = KeystoreRow.BACKINGS.flatMap { backing ->
        val base = KeystoreRequest(service.type, service.algorithm, block.authorizations, backing)
        when {
            block.keySizes.isNotEmpty() -> block.keySizes.map { base.copy(keySize = it) }
            block.curves.isNotEmpty() -> block.curves.map { base.copy(curve = it) }
            else -> listOf(base)
        }
    }

    private fun attempt(provider: Provider, request: KeystoreRequest, alias: String, sdkInt: Int): KeystoreRow {
        val started = System.nanoTime()
        val made = Attempt.of { maker.generate(provider, request, alias, sdkInt) }
        Attempt.of { maker.delete(provider, alias) }
        val millis = (System.nanoTime() - started) / NANOS_PER_MILLI
        return row(provider, request, made.exceptionOrNull()?.let { refusal(it, provider, request) }.orEmpty(), millis)
    }

    private fun row(provider: Provider, request: KeystoreRequest, error: String, millis: Long = 0) = KeystoreRow(provider.name, request.type, request.algorithm, request.backing,
        request.keySize, request.curve, supported = error.isEmpty(), error = error, millis = millis)

    /** The coded reason, as preparation's SecureKey codes it: a member this API lacks, StrongBox absent, else the keystore refusing this key. */
    private fun refusal(failure: Throwable, provider: Provider, request: KeystoreRequest): String {
        if (failure is KeystoreMaker.AbsentMember) return ErrorText.clean(failure.message.orEmpty())
        val chain = generateSequence(failure) { it.cause }.toList()
        if (chain.any { it.javaClass.simpleName == STRONGBOX_UNAVAILABLE }) return ErrorText.of(failure, "strongbox_unavailable: ${provider.name} ${request.backing}: ")
        val size = (request.keySize?.toString() ?: request.curve).takeIf { it.isNotEmpty() }?.let { "/$it" }.orEmpty()
        return ErrorText.of(chain.last(), "keystore_unsupported: ${request.type} ${request.algorithm}$size ${request.backing}: ")
    }

    private fun aliases(capture: CapturedEnvironment, service: ServiceRequirement): List<String> =
        capture.providers.firstOrNull { it.name == service.provider }?.services
            ?.firstOrNull { ServiceKey.fold(it.type) == ServiceKey.fold(service.type) && ServiceKey.fold(it.algorithm) == ServiceKey.fold(service.algorithm) }?.aliases.orEmpty()

    private companion object {
        const val PREFIX = "cryptobench-trial-"
        const val STRONGBOX_FEATURE = "android.hardware.strongbox_keystore"
        const val STRONGBOX_UNAVAILABLE = "StrongBoxUnavailableException"
        const val NANOS_PER_MILLI = 1_000_000L
        val GENERATORS = setOf(ServiceKey.fold("KeyGenerator"), ServiceKey.fold("KeyPairGenerator"))
    }
}
