package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

/** A misspelt section, key or choice fails by name instead of quietly falling back to defaults. */
class MalformedDocumentsTest {

    private val codec = YamlCodec()

    /** A misspelt section, key or choice fails by name instead of quietly falling back to defaults. */
    @Test
    fun malformedDocumentsAreRefusedByName() {
        val global = "schemaVersion: 1\nselection: {testSet: a.yaml}\n"
        listOf<Pair<() -> Any, String>>(
            { GlobalDocument.parse(codec.load(global + "rn: {}\n")) } to "unknown_section: [rn], known [selection, run, policy, analysis]",
            { GlobalDocument.parse(codec.load(global + "run: {inputSize: [1]}\n")) } to "unknown_keys: run [inputSize], known [inputSizes, phases, metrics, processRepetitions, seed, harness]",
            { GlobalDocument.parse(codec.load(global + "policy: {onFailure: retry}\n")) } to "invalid: policy.onFailure retry, one of [stop, skip]",
            { GlobalDocument.parse(codec.load(global + "policy: {onUnavailable: skip}\n")) } to "unknown_keys: policy [onUnavailable], known [onFailure]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {headline: average}}\n")) } to "invalid: analysis.statistic.headline average, one of [auto, median, mean]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {meanUpToCovPercent: 0}}\n")) } to "not_positive: meanUpToCovPercent 0.0 at analysis.statistic",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {covLimit: 5}}\n")) } to "unknown_keys: analysis.statistic [covLimit], known [headline, meanUpToCovPercent]",
            { GlobalDocument.parse(codec.load(global + "analysis: {stat: {}}\n")) } to "unknown_keys: analysis [stat], known [statistic, charts, dir]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [bars]}\n")) } to "invalid: analysis.charts bars, one of [iqrBars, throughput, latency, stability]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [iqrBars, iqrbars]}\n")) } to "duplicate: charts [iqrBars, iqrBars] at analysis",
            { GlobalDocument.parse(codec.load(global + "analysis: {dir: ' '}\n")) } to "blank: dir at analysis",
            { GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml, exclude: [{type: Mac}, {}]}\n")) } to "empty_rule: give provider, type or name at selection.exclude[1]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) } to "unknown_keys: overrides[0].set [keySize], known [keySizes, inputSizes, key, parameters, operations, harness]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {iterations: 0}}\n")) } to "not_positive: iterations 0 at run.harness",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {profile: none}}\n")) } to "unknown_keys: run.harness [profile], known [iterations, warmupIterations, profiling]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {harness: {profiling: flame}}}\n")) } to "invalid: profiling flame, known [none, MethodTracing, StackSampling] at overrides[0].set.harness",
            { codec.load("- one\n- two\n") } to "not_a_mapping: the document is not a set of key: value entries",
        ).forEach { (parse, expected) ->
            assertEquals(expected, assertThrows(IllegalArgumentException::class.java) { parse() }.message)
        }
        val duplicate = assertThrows(RuntimeException::class.java) { codec.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(duplicate, duplicate.contains("duplicate key"))
    }
}
