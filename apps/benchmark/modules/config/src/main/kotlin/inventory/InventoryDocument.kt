package io.github.junekim0007.cryptobench.config.inventory

import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.inventory.dto.InventoryEntry
import io.github.junekim0007.cryptobench.config.source.KeystoreRow
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ProviderTree
import io.github.junekim0007.cryptobench.document.DocumentFields.boolean
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumbers
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.string

object InventoryDocument : DocumentHandler<Inventory> {

    override val schemaVersion: Int = 2

    private const val GENERATED_FROM = "generatedFrom"
    private const val PROVIDERS = "providers"
    private const val WARNINGS = "warnings"
    private const val RUNS = "runs"
    private const val KEY_SIZES = "keySizes"
    private const val INPUT_SIZES = "inputSizes"
    private const val KEY_ALGORITHM = "keyAlgorithm"
    private const val KEY_PROVIDER = "keyProvider"
    private const val PROVIDER_CHOSE = "providerChose"
    private const val BARE_NAME = "bareName"
    private const val REASON = "reason"
    private const val ALIASES = "aliases"
    private const val KEYSTORE = "keystore"
    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val ALGORITHM = "algorithm"
    private const val BACKING = "backing"
    private const val KEY_SIZE = "keySize"
    private const val CURVE = "curve"
    private const val SUPPORTED = "supported"
    private const val ERROR = "error"

    override fun of(value: Inventory): Map<String, Any> = linkedMapOf<String, Any>(
        GENERATED_FROM to InventorySourceDocument.of(value.generatedFrom),
        PROVIDERS to ProviderTree.of(value.providers, ::entry),
    ).apply {
        if (value.warnings.isNotEmpty()) put(WARNINGS, value.warnings)
        if (value.keystore.isNotEmpty()) put(KEYSTORE, value.keystore.map(::keystoreRow))
    }

    override fun parse(document: Map<String, Any>): Inventory = Inventory(
        generatedFrom = InventorySourceDocument.parse(section(document, GENERATED_FROM)),
        providers = ProviderTree.parse(section(document, PROVIDERS), PROVIDERS, ::entryOf),
        warnings = optionalStrings(document, WARNINGS),
        keystore = optionalSections(document, KEYSTORE).map(::keystoreRowOf),
    )

    private fun entry(entry: InventoryEntry): Map<String, Any> = LinkedHashMap<String, Any>().apply {
        put(RUNS, entry.runs)
        if (entry.keySizes.isNotEmpty()) put(KEY_SIZES, entry.keySizes)
        if (entry.inputSizes.isNotEmpty()) put(INPUT_SIZES, entry.inputSizes)
        if (entry.keyAlgorithm.isNotEmpty()) put(KEY_ALGORITHM, entry.keyAlgorithm)
        if (entry.keyProvider.isNotEmpty()) put(KEY_PROVIDER, entry.keyProvider)
        if (entry.providerChose.isNotEmpty()) put(PROVIDER_CHOSE, entry.providerChose)
        if (entry.bareName) put(BARE_NAME, true)
        if (entry.reason.isNotEmpty()) put(REASON, entry.reason)
        if (entry.aliases.isNotEmpty()) put(ALIASES, entry.aliases)
    }

    private fun keystoreRow(row: KeystoreRow): Map<String, Any> = linkedMapOf<String, Any>(PROVIDER to row.provider, TYPE to row.type, ALGORITHM to row.algorithm, BACKING to row.backing).apply {
        row.keySize?.let { put(KEY_SIZE, it) }
        if (row.curve.isNotEmpty()) put(CURVE, row.curve)
        put(SUPPORTED, row.supported)
        if (row.error.isNotEmpty()) put(ERROR, row.error)
    }

    private fun keystoreRowOf(document: Map<String, Any>): KeystoreRow = KeystoreRow(string(document, PROVIDER), string(document, TYPE), string(document, ALGORITHM),
        string(document, BACKING), optionalNumber(document, KEY_SIZE)?.toInt(), optionalString(document, CURVE), boolean(document, SUPPORTED), optionalString(document, ERROR))

    private fun entryOf(document: Map<String, Any>): InventoryEntry = InventoryEntry(
        runs = boolean(document, RUNS),
        keySizes = optionalNumbers(document, KEY_SIZES),
        inputSizes = optionalNumbers(document, INPUT_SIZES),
        keyAlgorithm = optionalString(document, KEY_ALGORITHM),
        keyProvider = optionalString(document, KEY_PROVIDER),
        providerChose = optionalString(document, PROVIDER_CHOSE),
        bareName = optionalBoolean(document, BARE_NAME),
        reason = optionalString(document, REASON),
        aliases = optionalStrings(document, ALIASES),
    )
}
