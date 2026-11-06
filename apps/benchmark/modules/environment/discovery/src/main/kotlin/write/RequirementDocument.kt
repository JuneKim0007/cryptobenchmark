package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.KeyCacheStats
import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import io.github.junekim0007.cryptobench.discovery.contract.ServiceRequirement
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.number
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalString
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.optionalStrings
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.section
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.sections
import io.github.junekim0007.cryptobench.discovery.write.DocumentFields.string

object RequirementDocument {

    private const val SCHEMA_VERSION = "schemaVersion"
    private const val CAPTURED_AT_MILLIS = "capturedAtMillis"
    private const val DEVICE_CLOCK_MILLIS = "deviceClockMillis"
    private const val MILLIS = "millis"
    private const val KEY_CACHE = "keyCache"
    private const val GENERATED = "generated"
    private const val REFUSED = "refused"
    private const val REUSED = "reused"
    private const val GENERATION_MILLIS = "generationMillis"
    const val SERVICES = "services"
    private const val PROVIDER = "provider"
    private const val TYPE = "type"
    private const val ALGORITHM = "algorithm"
    private const val TRANSFORMATION_OF = "transformationOf"
    private const val CLASS_NAME = "className"
    private const val CLASS_RUN = "classRun"
    private const val STATUS = "status"
    private const val REASON = "reason"
    private const val DETAIL = "detail"
    private const val CONDITIONS = "conditions"
    private const val KEY = "key"
    private const val RUN_WITH = "runWith"
    private const val KEYS_TRIED = "keysTried"
    private const val FACTS = "facts"
    private const val ALIASES = "aliases"

    fun of(report: RequirementReport): Map<String, Any> = header(report) + (SERVICES to report.services.map { serviceDocument(it) })

    /** Everything but the services, which a writer emits one at a time. */
    fun header(report: RequirementReport): Map<String, Any> = linkedMapOf(
        SCHEMA_VERSION to report.schemaVersion,
        CAPTURED_AT_MILLIS to report.capturedAtMillis,
        DEVICE_CLOCK_MILLIS to report.deviceClockMillis,
        MILLIS to report.millis,
        KEY_CACHE to linkedMapOf(GENERATED to report.keyCache.generated, REFUSED to report.keyCache.refused, REUSED to report.keyCache.reused, GENERATION_MILLIS to report.keyCache.generationMillis),
    )

    fun parse(document: Map<String, Any>): RequirementReport {
        val schemaVersion = number(document, SCHEMA_VERSION).toInt()
        require(schemaVersion == RequirementReport.SCHEMA_VERSION) {
            "unsupported_schema_version: $schemaVersion, this build reads ${RequirementReport.SCHEMA_VERSION}"
        }
        val cache = section(document, KEY_CACHE)
        return RequirementReport(
            capturedAtMillis = number(document, CAPTURED_AT_MILLIS).toLong(),
            deviceClockMillis = number(document, DEVICE_CLOCK_MILLIS).toLong(),
            services = sections(document, SERVICES).map { serviceEntry(it) },
            millis = number(document, MILLIS).toLong(),
            keyCache = KeyCacheStats(number(cache, GENERATED).toInt(), number(cache, REFUSED).toInt(), number(cache, REUSED).toInt(), number(cache, GENERATION_MILLIS).toLong()),
            schemaVersion = schemaVersion,
        )
    }

    fun serviceDocument(service: ServiceRequirement): Map<String, Any> {
        val document = linkedMapOf<String, Any>(PROVIDER to service.provider, TYPE to service.type, ALGORITHM to service.algorithm)
        fun put(name: String, value: Any, present: Boolean) { if (present) document[name] = value }
        put(TRANSFORMATION_OF, service.transformationOf, service.transformationOf.isNotEmpty())
        put(CLASS_NAME, service.className, service.className.isNotEmpty())
        put(CLASS_RUN, service.classRun, service.classRun.isNotEmpty())
        document[STATUS] = service.status
        put(REASON, service.reason, service.reason.isNotEmpty())
        put(DETAIL, service.detail, service.detail.isNotEmpty())
        put(CONDITIONS, service.conditions, service.conditions.isNotEmpty())
        put(KEY, service.key, service.key.isNotEmpty())
        put(RUN_WITH, service.runWith, service.runWith.isNotEmpty())
        put(KEYS_TRIED, service.keysTried, service.keysTried.isNotEmpty())
        put(FACTS, service.facts, service.facts.isNotEmpty())
        put(ALIASES, service.aliases, service.aliases.isNotEmpty())
        document[MILLIS] = service.millis
        return document
    }

    private fun serviceEntry(document: Map<String, Any>): ServiceRequirement = ServiceRequirement(
        provider = string(document, PROVIDER),
        type = string(document, TYPE),
        algorithm = string(document, ALGORITHM),
        status = string(document, STATUS),
        className = optionalString(document, CLASS_NAME),
        classRun = optionalString(document, CLASS_RUN),
        transformationOf = optionalString(document, TRANSFORMATION_OF),
        reason = optionalString(document, REASON),
        detail = optionalString(document, DETAIL),
        conditions = optionalStrings(document, CONDITIONS),
        key = optionalSection(document, KEY).orEmpty(),
        runWith = optionalSection(document, RUN_WITH).orEmpty(),
        keysTried = optionalSections(document, KEYS_TRIED),
        facts = optionalSection(document, FACTS).orEmpty(),
        aliases = optionalSections(document, ALIASES),
        millis = number(document, MILLIS).toLong(),
    )
}
