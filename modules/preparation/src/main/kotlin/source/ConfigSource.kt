package io.github.junekim0007.cryptobench.preparation.source

import io.github.junekim0007.cryptobench.preparation.measurement.Metric
import io.github.junekim0007.cryptobench.preparation.measurement.Phase
import io.github.junekim0007.cryptobench.preparation.request.BenchmarkRequest
import io.github.junekim0007.cryptobench.preparation.request.Selection
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.asSection
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.number
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.numbers
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.optionalNumbers
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.optionalSection
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.section
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.string
import io.github.junekim0007.cryptobench.preparation.source.ConfigFields.strings
import io.github.junekim0007.cryptobench.preparation.request.OnFailure
import io.github.junekim0007.cryptobench.preparation.yaml.YamlCodec
import java.io.File

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
        require(selections.isNotEmpty()) { "nothing_selected" }
        return BenchmarkRequest(
            selections = selections,
            inputSizes = numbers(run, "inputSizes"),
            phases = strings(run, "phases").mapTo(LinkedHashSet()) { enumOf<Phase>("phase", it) },
            metrics = strings(run, "metrics").mapTo(LinkedHashSet()) { enumOf<Metric>("metric", it) },
            processRepetitions = number(run, "processRepetitions").toInt(),
            seed = number(run, "seed").toLong(),
            onFailure = enumOf<OnFailure>("onFailure", string(section(document, "policy"), "onFailure")),
        )
    }

    private fun selections(providers: Map<String, Any>): List<Selection> =
        providers.flatMap { (provider, types) ->
            asSection(types, provider).flatMap { (type, entries) ->
                asSection(entries, "$provider.$type").map { (name, value) ->
                    val entry = asSection(value, "$provider.$type.$name")
                    Selection(
                        type = type,
                        algorithm = name,
                        providers = listOf(provider),
                        keySizes = optionalNumbers(entry, "keySizes"),
                        inputSizes = optionalNumbers(entry, "inputSizes"),
                        keyParameters = optionalSection(entry, "key"),
                        parameters = optionalSection(entry, "parameters"),
                    )
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
