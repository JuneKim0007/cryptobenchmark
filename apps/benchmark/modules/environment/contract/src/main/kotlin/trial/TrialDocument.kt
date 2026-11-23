package io.github.junekim0007.cryptobench.contract.trial

import io.github.junekim0007.cryptobench.document.SchemaVersion
import io.github.junekim0007.cryptobench.document.versioned.DocumentReader
import io.github.junekim0007.cryptobench.document.versioned.YamlFiles
import io.github.junekim0007.cryptobench.document.DocumentFields.boolean
import io.github.junekim0007.cryptobench.document.DocumentFields.number
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalBoolean
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalNumber
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.document.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.document.DocumentFields.section
import io.github.junekim0007.cryptobench.document.DocumentFields.sections
import io.github.junekim0007.cryptobench.document.DocumentFields.sectionsIfKeyPresent
import io.github.junekim0007.cryptobench.document.DocumentFields.string
import java.io.File

object TrialDocument : DocumentReader<TrialReport> {

    override val schemaVersion = TrialReport.SCHEMA_VERSION

    private const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    private const val SERVICES = "services"
    private const val DEFAULT_RUN_INPUT_SIZE = "defaultRunInputSize"

    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val ALGORITHM = "algorithm"
    private const val INSTANTIATES = "instantiates"
    private const val ERROR = "error"
    private const val TRANSFORMATIONS = "transformations"
    private const val NAME = "name"

    private const val DEFAULT_RUN = "defaultRun"
    private const val WORKS = "works"
    private const val KEY_ALGORITHM = "keyAlgorithm"
    private const val KEY_PROVIDER = "keyProvider"
    private const val KEY_SIZE = "keySize"
    private const val FIXED_KEY_SIZE = "fixedKeySize"
    private const val INPUT_SIZE = "inputSize"
    private const val PROVIDER_CHOSE = "providerChose"
    private const val BARE_NAME = "bareName"
    private const val KEY_MATERIAL = "keyMaterial"
    private const val KEY_FORMAT = "keyFormat"
    private const val TRIED_KEYS = "triedKeys"
    private const val SIZE = "size"
    private const val REFUSED = "refused"

    private const val KEYSTORE = "keystore"
    private const val ROWS = "rows"
    private const val ABSENT = "absent"
    private const val BACKING = "backing"
    private const val CURVE = "curve"
    private const val SUPPORTED = "supported"
    private const val MILLIS = "millis"

    fun of(report: TrialReport): Map<String, Any> = linkedMapOf<String, Any>(
        SchemaVersion.FIELD to report.schemaVersion,
        CAPTURED_AT_MILLIS to report.capturedAtMillis,
    ).apply {
        report.defaultRunInputSize?.let { put(DEFAULT_RUN_INPUT_SIZE, it) }
        put(SERVICES, report.services.map { serviceDocument(it) })
        report.keystore?.let { put(KEYSTORE, keystoreDocument(it)) }
    }

    // the one read of a stored file: VersionedFile on the DOCUMENT codec
    fun read(file: File): TrialReport = YamlFiles().readOnly(file, this).read()

    override fun parse(document: Map<String, Any>): TrialReport {
        val schemaVersion = number(document, SchemaVersion.FIELD).toInt()
        return TrialReport(
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            services = sections(document, SERVICES).map { serviceEntry(it) },
            schemaVersion = schemaVersion,
            defaultRunInputSize = optionalNumber(document, DEFAULT_RUN_INPUT_SIZE)?.toInt(),
            // required: a trial written before the keystore trial is refused
            keystore = keystoreSection(section(document, KEYSTORE)),
        )
    }

    private fun keystoreDocument(section: KeystoreSection): Map<String, Any> =
        if (section.absent.isNotEmpty()) linkedMapOf(ABSENT to section.absent) else linkedMapOf(ROWS to section.rows.map { keystoreRowDocument(it) })

    private fun keystoreSection(document: Map<String, Any>): KeystoreSection =
        KeystoreSection(rows = sectionsIfKeyPresent(document, ROWS).map { keystoreRow(it) }, absent = optionalString(document, ABSENT))

    private fun keystoreRowDocument(row: KeystoreRow): Map<String, Any> {
        val document = linkedMapOf<String, Any>(PROVIDER to row.provider, TYPE to row.type, ALGORITHM to row.algorithm, BACKING to row.backing)
        row.keySize?.let { document[KEY_SIZE] = it }
        if (row.curve.isNotEmpty()) document[CURVE] = row.curve
        document[SUPPORTED] = row.supported
        if (!row.supported) document[ERROR] = row.error
        document[MILLIS] = row.millis
        return document
    }

    private fun keystoreRow(document: Map<String, Any>): KeystoreRow = KeystoreRow(
        provider = string(document, PROVIDER),
        type = string(document, TYPE),
        algorithm = string(document, ALGORITHM),
        backing = string(document, BACKING),
        keySize = optionalNumber(document, KEY_SIZE)?.toInt(),
        curve = optionalString(document, CURVE),
        supported = boolean(document, SUPPORTED),
        error = optionalString(document, ERROR),
        millis = number(document, MILLIS).toLong(),
    )

    private fun serviceDocument(service: ServiceTrialEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(
            PROVIDER to service.provider,
            TYPE to service.type,
            ALGORITHM to service.algorithm,
        )
        outcome(document, service.outcome)
        service.defaultRun?.let { document[DEFAULT_RUN] = defaultRunDocument(it) }
        if (service.transformations.isNotEmpty()) {
            document[TRANSFORMATIONS] = service.transformations.map { transformationDocument(it) }
        }
        return document
    }

    private fun serviceEntry(document: Map<String, Any>): ServiceTrialEntry = ServiceTrialEntry(
        provider = string(document, PROVIDER),
        type = string(document, TYPE),
        algorithm = string(document, ALGORITHM),
        outcome = outcome(document),
        transformations = sectionsIfKeyPresent(document, TRANSFORMATIONS).map { transformationEntry(it) },
        defaultRun = optionalSection(document, DEFAULT_RUN)?.let { defaultRunEntry(it) },
    )

    private fun transformationDocument(transformation: TransformationTrialEntry): Map<String, Any> {
        val document = linkedMapOf<String, Any>(NAME to transformation.name)
        outcome(document, transformation.outcome)
        transformation.defaultRun?.let { document[DEFAULT_RUN] = defaultRunDocument(it) }
        return document
    }

    private fun transformationEntry(document: Map<String, Any>): TransformationTrialEntry =
        TransformationTrialEntry(
            name = string(document, NAME),
            outcome = outcome(document),
            defaultRun = optionalSection(document, DEFAULT_RUN)?.let { defaultRunEntry(it) },
        )

    private fun defaultRunDocument(run: DefaultRunOutcome): Map<String, Any> {
        val document = linkedMapOf<String, Any>(WORKS to run.works)
        if (run.keyAlgorithm.isNotEmpty()) document[KEY_ALGORITHM] = run.keyAlgorithm
        if (run.keyProvider.isNotEmpty()) document[KEY_PROVIDER] = run.keyProvider
        run.keySize?.let { document[KEY_SIZE] = it }
        run.fixedKeySize?.let { document[FIXED_KEY_SIZE] = it }
        run.inputSize?.let { document[INPUT_SIZE] = it }
        if (run.providerChose.isNotEmpty()) document[PROVIDER_CHOSE] = run.providerChose
        if (run.bareName) document[BARE_NAME] = true
        if (run.keyMaterial.isNotEmpty()) document[KEY_MATERIAL] = run.keyMaterial
        if (run.keyFormat.isNotEmpty()) document[KEY_FORMAT] = run.keyFormat
        if (run.triedKeys.isNotEmpty()) document[TRIED_KEYS] = run.triedKeys.map { triedKeyDocument(it) }
        if (!run.works) document[ERROR] = run.error
        return document
    }

    private fun defaultRunEntry(document: Map<String, Any>): DefaultRunOutcome = DefaultRunOutcome(
        works = boolean(document, WORKS),
        keyAlgorithm = optionalString(document, KEY_ALGORITHM),
        keyProvider = optionalString(document, KEY_PROVIDER),
        keySize = optionalNumber(document, KEY_SIZE)?.toInt(),
        fixedKeySize = optionalNumber(document, FIXED_KEY_SIZE)?.toInt(),
        inputSize = optionalNumber(document, INPUT_SIZE)?.toInt(),
        providerChose = optionalString(document, PROVIDER_CHOSE),
        bareName = optionalBoolean(document, BARE_NAME),
        keyMaterial = optionalString(document, KEY_MATERIAL),
        keyFormat = optionalString(document, KEY_FORMAT),
        triedKeys = sectionsIfKeyPresent(document, TRIED_KEYS).map { triedKeyEntry(it) },
        error = optionalString(document, ERROR),
    )

    private fun triedKeyDocument(key: TriedKey): Map<String, Any> {
        val document = linkedMapOf<String, Any>(SIZE to key.size)
        if (key.keyMaterial.isNotEmpty()) document[KEY_MATERIAL] = key.keyMaterial
        if (key.keyFormat.isNotEmpty()) document[KEY_FORMAT] = key.keyFormat
        if (key.refused) document[REFUSED] = true
        return document
    }

    private fun triedKeyEntry(document: Map<String, Any>): TriedKey = TriedKey(
        size = number(document, SIZE).toInt(),
        keyMaterial = optionalString(document, KEY_MATERIAL),
        keyFormat = optionalString(document, KEY_FORMAT),
        refused = optionalBoolean(document, REFUSED),
    )

    private fun outcome(document: MutableMap<String, Any>, outcome: TrialOutcome) {
        document[INSTANTIATES] = outcome.instantiates
        if (!outcome.instantiates) {
            document[ERROR] = outcome.error
        }
    }

    private fun outcome(document: Map<String, Any>): TrialOutcome =
        TrialOutcome(instantiates = boolean(document, INSTANTIATES), error = optionalString(document, ERROR))
}
