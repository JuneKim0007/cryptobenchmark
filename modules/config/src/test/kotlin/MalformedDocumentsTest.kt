package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class MalformedDocumentsTest {

    private val codec = YamlCodec()

    @Test
    fun malformedDocumentsAreRefusedByName() {
        val global = "schemaVersion: 1\nselection: {testSet: a.yaml}\n"
        listOf<Pair<() -> Any, String>>(
            { GlobalDocument.parse(codec.load(global + "rn: {}\n")) } to "unknown_section: [rn], known [selection, run, policy, analysis, providers]",
            { GlobalDocument.parse(codec.load(global + "run: {inputSize: [1]}\n")) } to "unknown_keys: run [inputSize], known [inputSizes, phases, metrics, processRepetitions, isolation, seed, scopedRepetitions, harness]",
            { GlobalDocument.parse(codec.load(global + "policy: {onFailure: retry}\n")) } to "invalid: policy.onFailure retry, one of [stop, skip]",
            { GlobalDocument.parse(codec.load(global + "policy: {onUnavailable: skip}\n")) } to "unknown_keys: policy [onUnavailable], known [onFailure]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {headline: average}}\n")) } to "invalid: analysis.statistic.headline average, one of [auto, median, mean]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {meanUpToCovPercent: 0}}\n")) } to "not_positive: meanUpToCovPercent 0.0 at analysis.statistic",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {covLimit: 5}}\n")) } to "unknown_keys: analysis.statistic [covLimit], known [headline, meanUpToCovPercent]",
            { GlobalDocument.parse(codec.load(global + "analysis: {stat: {}}\n")) } to "unknown_keys: analysis [stat], known [statistic, charts, dir, units]",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {latency: s}}\n")) } to "invalid: analysis.units.latency s, one of [ms, us, ns]",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {throughput: GB/s}}\n")) } to "invalid: analysis.units.throughput GB/s, one of [MB/s, MiB/s, ops/s]",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {time: ms}}\n")) } to "unknown_keys: analysis.units [time], known [latency, throughput]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [bars]}\n")) } to "invalid: analysis.charts bars, one of [iqrBars, throughput, latency, stability]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [iqrBars, iqrbars]}\n")) } to "duplicate: charts [iqrBars, iqrBars] at analysis",
            { GlobalDocument.parse(codec.load(global + "analysis: {dir: ' '}\n")) } to "blank: dir at analysis",
            { GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml, exclude: [{type: Mac}, {}]}\n")) } to "empty_rule: give provider, type or name at selection.exclude[1]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) } to "unknown_keys: overrides[0].set [keySize], known [keySizes, inputSizes, key, parameters, operations, harness]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {iterations: 0}}\n")) } to "not_positive: iterations 0 at run.harness",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {profile: none}}\n")) } to "unknown_keys: run.harness [profile], known [iterations, warmupIterations, profiling, energy, cpu]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {capture: always}}}\n")) } to "invalid: energy.capture always, known [none, measured, dry] at run.harness.energy",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {capture: off}}}\n")) } to "invalid: energy.capture false (YAML reads off/on/yes/no as booleans), write one of [none, measured, dry] at run.harness.energy",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {window: 5}}}\n")) } to "unknown_keys: run.harness.energy [window], known [capture, windowSeconds, warmupSeconds, cooldownSeconds, source]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {source: wattmeter}}}\n")) } to "invalid: energy.source wattmeter, known [rails, manafa] at run.harness.energy",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {harness: {profiling: flame}}}\n")) } to "invalid: profiling flame, known [none, MethodTracing, StackSampling] at overrides[0].set.harness",
            { GlobalDocument.parse(codec.load(global + "providers: {platform: []}\n")) } to "unknown_keys: providers [platform], known [bundled]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: a:b, create: a.B}]}\n")) } to "invalid_artifact: a:b, expected group:name:version at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: B}]}\n")) } to "invalid_create: B, expected fully.qualified.Class or fully.qualified.Class#staticFactory at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: 'a.B#'}]}\n")) } to "invalid_create: a.B#, expected fully.qualified.Class or fully.qualified.Class#staticFactory at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, alias: ' '}]}\n")) } to "invalid_alias: ' ', expected a non-blank name without whitespace at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, position: 1}]}\n")) } to "unknown_keys: providers.bundled[0] [position], known [artifact, create, alias]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{create: a.B}]}\n")) } to "missing_field: artifact at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B}, {artifact: 'a:b:1', create: a.C}]}\n")) } to "duplicate_artifact: [a:b:1] at providers.bundled",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, alias: X}, {artifact: 'c:d:1', create: c.D, alias: X}]}\n")) } to "duplicate_alias: [X] at providers.bundled",
            { codec.load("- one\n- two\n") } to "not_a_mapping: the document is not a set of key: value entries",
        ).forEach { (parse, expected) ->
            assertEquals(expected, assertThrows(IllegalArgumentException::class.java) { parse() }.message)
        }
        val duplicate = assertThrows(RuntimeException::class.java) { codec.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(duplicate, duplicate.contains("duplicate key"))
    }
}
