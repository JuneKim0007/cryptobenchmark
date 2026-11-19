import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.preparation.global.GlobalReader
import io.github.junekim0007.cryptobench.preparation.inbound.InboundFile
import org.junit.Assert.assertEquals
import org.junit.Test

/** Characterization: one run value through configure (GlobalDocument) and through preparation (GlobalReader on effective.yaml); today's verdicts. */
class RunRulesTest {

    private fun configure(run: String): String = verdict {
        GlobalDocument.parse(YamlCodec.DOCUMENT.load("schemaVersion: 1\nselection: {testSet: t.yaml}\nrun: {$run, orderSeed: 1}\n"))
    }

    private fun prepare(run: String): String = verdict {
        GlobalReader.read(InboundFile.read("effective.yaml", EFFECTIVE.replace("RUN", run)))
    }

    private fun verdict(read: () -> Any): String = try {
        read()
        "accepted"
    } catch (refused: IllegalArgumentException) {
        refused.message!!
    }

    @Test
    fun configureRefusesEveryRunRuleAndPreparationStillRefusesAnUnknownPhase() {
        val table = listOf(
            "inputSizes: [64], phases: [WARM], processRepetitions: 1",
            "inputSizes: [64], phases: [COLD], processRepetitions: 1",
            "inputSizes: [64, 64], phases: [WARM], processRepetitions: 1",
            "inputSizes: [64], phases: [WARM], processRepetitions: 0",
        ).joinToString("\n") { run -> "$run | ${configure(run)} | ${prepare(run)}" }
        assertEquals(EXPECTED, table)
    }

    private companion object {
        val EFFECTIVE = """
            schemaVersion: 2
            generatedFrom: {global: global.yaml, testSet: t.yaml, inventory: inventory.yaml, capture: probe_x.yaml, trial: trial_x.yaml,
              device: {model: m, manufacturer: m, hardware: h, sdkInt: 0, release: r, javaVersion: '17'}}
            run: {RUN, metrics: [TIME], seed: 0, variants: [fixed]}
            policy: {onFailure: skip}
            providers: {}
        """.trimIndent() + "\n"
        // run | configure | preparation
        val EXPECTED = """
            inputSizes: [64], phases: [WARM], processRepetitions: 1 | accepted | accepted
            inputSizes: [64], phases: [COLD], processRepetitions: 1 | unknown_phase: COLD, one of [WARM] | unknown_phase: COLD, one of [WARM]
            inputSizes: [64, 64], phases: [WARM], processRepetitions: 1 | duplicate: inputSizes [64, 64] | accepted
            inputSizes: [64], phases: [WARM], processRepetitions: 0 | not_positive: processRepetitions 0 | accepted
        """.trimIndent()
    }
}
