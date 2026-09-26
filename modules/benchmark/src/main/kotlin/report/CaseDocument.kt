package io.github.junekim0007.cryptobench.benchmark.report

import org.yaml.snakeyaml.LoaderOptions
import org.yaml.snakeyaml.Yaml
import org.yaml.snakeyaml.constructor.SafeConstructor

internal object CaseDocument {

    fun load(text: String): Map<String, Any> = section(Yaml(SafeConstructor(LoaderOptions())).load<Any?>(text))

    @Suppress("UNCHECKED_CAST")
    fun section(value: Any?): Map<String, Any> =
        value as? Map<String, Any> ?: throw IllegalArgumentException("not_a_mapping: $value")

    fun sections(value: Any?): List<Map<String, Any>> = list(value).map { element -> section(element) }

    fun samples(value: Any?): List<Long> = list(value).map { sample -> (sample as Number).toLong() }

    fun iterations(value: Any?): Int = integer(value) ?: 1

    fun row(case: Map<String, Any>, iterations: Int, nanosPerOperation: List<Long>): ResultRow = ResultRow(
        id = case["id"].toString(),
        type = case["type"].toString(),
        algorithm = case["algorithm"].toString(),
        provider = case["provider"].toString(),
        operation = case["operation"].toString(),
        keySize = integer(case["keySize"]),
        inputSize = integer(case["inputSize"]),
        iterations = iterations,
        nanosPerOperation = nanosPerOperation,
    )

    private fun list(value: Any?): List<Any> =
        (value as? List<*>)?.filterNotNull() ?: throw IllegalArgumentException("not_a_list: $value")

    private fun integer(value: Any?): Int? = (value as? Number)?.toInt()
}
