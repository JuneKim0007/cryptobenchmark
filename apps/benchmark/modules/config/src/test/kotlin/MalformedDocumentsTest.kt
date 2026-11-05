package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import org.junit.Assert.assertThrows
import org.junit.Assert.assertTrue
import org.junit.Test

class MalformedDocumentsTest {

    private val codec = YamlCodec()

    @Test
    fun malformedDocumentsAreRefusedByName() {
        val global = "schemaVersion: 1\nselection: {testSet: a.yaml}\n"
        listOf<Pair<() -> Any, String>>(
            { GlobalDocument.parse(codec.load(global + "rn: {}\n")) } to "unknown_section: [rn]",
            { GlobalDocument.parse(codec.load(global + "run: {inputSize: [1]}\n")) } to "unknown_keys: run [inputSize]",
            { GlobalDocument.parse(codec.load(global + "policy: {onFailure: retry}\n")) } to "invalid: policy.onFailure retry",
            { GlobalDocument.parse(codec.load(global + "policy: {onUnavailable: skip}\n")) } to "unknown_keys: policy [onUnavailable]",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {headline: average}}\n")) } to "invalid: analysis.statistic.headline average",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {meanUpToCovPercent: 0}}\n")) } to "not_positive: meanUpToCovPercent 0.0 at analysis.statistic",
            { GlobalDocument.parse(codec.load(global + "analysis: {statistic: {covLimit: 5}}\n")) } to "unknown_keys: analysis.statistic [covLimit]",
            { GlobalDocument.parse(codec.load(global + "analysis: {stat: {}}\n")) } to "unknown_keys: analysis [stat]",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {latency: s}}\n")) } to "invalid: analysis.units.latency s",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {throughput: GB/s}}\n")) } to "invalid: analysis.units.throughput GB/s",
            { GlobalDocument.parse(codec.load(global + "analysis: {units: {time: ms}}\n")) } to "unknown_keys: analysis.units [time]",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [bars]}\n")) } to "invalid: analysis.charts bars",
            { GlobalDocument.parse(codec.load(global + "analysis: {charts: [iqrBars, iqrbars]}\n")) } to "duplicate: charts [iqrBars, iqrBars] at analysis",
            { GlobalDocument.parse(codec.load(global + "analysis: {dir: ' '}\n")) } to "blank: dir at analysis",
            { GlobalDocument.parse(codec.load("schemaVersion: 1\nselection: {testSet: a.yaml, exclude: [{type: Mac}, {}]}\n")) } to "empty_rule",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {keySize: [1]}}\n")) } to "unknown_keys: overrides[0].set [keySize]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {profile: none}}\n")) } to "unknown_keys: run.harness [profile]",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {capture: off}}}\n")) } to "invalid: energy.capture false",
            { GlobalDocument.parse(codec.load(global + "run: {harness: {energy: {window: 5}}}\n")) } to "unknown_keys: run.harness.energy [window]",
            { TestSetDocument.parse(codec.load("schemaVersion: 1\noverrides:\n- {match: {type: Cipher}, set: {harness: {profiling: flame}}}\n")) } to "invalid: profiling flame",
            { GlobalDocument.parse(codec.load(global + "providers: {platform: []}\n")) } to "unknown_keys: providers [platform]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: a:b, create: a.B}]}\n")) } to "invalid_artifact: a:b",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: B}]}\n")) } to "invalid_create: B",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, alias: ' '}]}\n")) } to "invalid_alias: ' '",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, position: 1}]}\n")) } to "unknown_keys: providers.bundled[0] [position]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{create: a.B}]}\n")) } to "missing_field: artifact at providers.bundled[0]",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B}, {artifact: 'a:b:1', create: a.C}]}\n")) } to "duplicate_artifact: [a:b:1] at providers.bundled",
            { GlobalDocument.parse(codec.load(global + "providers: {bundled: [{artifact: 'a:b:1', create: a.B, alias: X}, {artifact: 'c:d:1', create: c.D, alias: X}]}\n")) } to "duplicate_alias: [X] at providers.bundled",
            { codec.load("- one\n- two\n") } to "not_a_mapping: the document is not a set of key: value entries",
        ).forEach { (parse, expected) ->
            val message = assertThrows(expected, IllegalArgumentException::class.java) { parse() }.message!!
            assertTrue(message, message.startsWith(expected))
        }
        val duplicate = assertThrows(RuntimeException::class.java) { codec.load("schemaVersion: 1\nschemaVersion: 1\n") }.message!!
        assertTrue(duplicate, duplicate.contains("duplicate key"))
    }
}
