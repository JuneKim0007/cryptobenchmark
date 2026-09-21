package io.github.junekim0007.cryptobench.benchmark.preparation.source

import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.Metric
import io.github.junekim0007.cryptobench.benchmark.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.benchmark.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.benchmark.preparation.request.Selection
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.asSection
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.boolean
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.number
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.numbers
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.optionalNumbers
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.section
import io.github.junekim0007.cryptobench.benchmark.preparation.source.ConfigFields.strings
import java.io.File

/**
 * default.yaml → request, read by key: preparation does not depend on the config module's classes.
 * Each enabled entry becomes one selection pinned to its provider; disabled entries are skipped.
 */
class ConfigSource {

    private val codec = YamlCodec()

    fun read(file: File): BenchmarkRequest = read(file.readText())

    fun read(text: String): BenchmarkRequest {
        val document = codec.load(text)
        val schemaVersion = number(document, "schemaVersion").toInt()
        require(schemaVersion == SUPPORTED_SCHEMA_VERSION) {
            "unsupported_config_schema: $schemaVersion, this build reads $SUPPORTED_SCHEMA_VERSION"
        }
        val run = section(document, "run")
        val selections = selections(section(document, "providers"))
        require(selections.isNotEmpty()) { "nothing_enabled" }
        return BenchmarkRequest(
            selections = selections,
            inputSizes = numbers(run, "inputSizes"),
            phases = strings(run, "phases").mapTo(LinkedHashSet()) { enumOf<Phase>("phase", it) },
            metrics = strings(run, "metrics").mapTo(LinkedHashSet()) { enumOf<Metric>("metric", it) },
            processRepetitions = number(run, "processRepetitions").toInt(),
            seed = number(run, "seed").toLong(),
        )
    }

    private fun selections(providers: Map<String, Any>): List<Selection> =
        providers.flatMap { (provider, types) ->
            asSection(types, provider).flatMap { (type, entries) ->
                asSection(entries, "$provider.$type").mapNotNull { (name, value) ->
                    val entry = asSection(value, "$provider.$type.$name")
                    if (!boolean(entry, "enabled")) {
                        null
                    } else {
                        Selection(
                            type = type,
                            algorithm = name,
                            providers = listOf(provider),
                            keySizes = optionalNumbers(entry, "keySizes"),
                            inputSizes = optionalNumbers(entry, "inputSizes"),
                        )
                    }
                }
            }
        }

    private inline fun <reified E : Enum<E>> enumOf(field: String, name: String): E =
        enumValues<E>().firstOrNull { it.name.equals(name, ignoreCase = true) }
            ?: throw IllegalArgumentException("unknown_$field: $name, one of ${enumValues<E>().map { it.name }}")

    companion object {
        const val SUPPORTED_SCHEMA_VERSION = 1
    }
}
