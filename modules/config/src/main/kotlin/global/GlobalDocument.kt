package io.github.junekim0007.cryptobench.config.global

import io.github.junekim0007.cryptobench.config.global.dto.AnalysisSettings
import io.github.junekim0007.cryptobench.config.global.dto.GlobalConfig
import io.github.junekim0007.cryptobench.config.global.dto.Policy
import io.github.junekim0007.cryptobench.config.global.dto.RunSettings
import io.github.junekim0007.cryptobench.config.global.dto.Selection
import io.github.junekim0007.cryptobench.config.testset.RuleDocument
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.expectKeys
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSection
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.optionalSections
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.section
import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.string
import io.github.junekim0007.cryptobench.config.yaml.DocumentHandler
import io.github.junekim0007.cryptobench.config.yaml.ReadOnlyYamlFile

object GlobalDocument : DocumentHandler<GlobalConfig> {

    override val schemaVersion: Int = 1

    private const val SELECTION = "selection"
    private const val RUN = "run"
    private const val POLICY = "policy"
    private const val ANALYSIS = "analysis"
    private const val TEST_SET = "testSet"
    private const val EXCLUDE = "exclude"

    private val SECTIONS: List<String> = listOf(SELECTION, RUN, POLICY, ANALYSIS)

    override fun of(value: GlobalConfig): Map<String, Any> = linkedMapOf(
        SELECTION to linkedMapOf(TEST_SET to value.selection.testSet, EXCLUDE to value.selection.exclude.map { RuleDocument.of(it) }),
        RUN to RunDocument.of(value.run),
        POLICY to PolicyDocument.of(value.policy),
        ANALYSIS to AnalysisDocument.of(value.analysis),
    )

    override fun parse(document: Map<String, Any>): GlobalConfig {
        val unknown = document.keys.filter { it != ReadOnlyYamlFile.SCHEMA_VERSION && it !in SECTIONS }
        require(unknown.isEmpty()) { "unknown_section: $unknown, known $SECTIONS" }
        return GlobalConfig(
            selection = selection(section(document, SELECTION)),
            run = optionalSection(document, RUN)?.let { RunDocument.parse(it, RUN) } ?: RunSettings(),
            policy = optionalSection(document, POLICY)?.let { PolicyDocument.parse(it, POLICY) } ?: Policy(),
            analysis = optionalSection(document, ANALYSIS)?.let { AnalysisDocument.parse(it, ANALYSIS) } ?: AnalysisSettings(),
        )
    }

    private fun selection(document: Map<String, Any>): Selection {
        expectKeys(document, listOf(TEST_SET, EXCLUDE), SELECTION)
        return Selection(string(document, TEST_SET), RuleDocument.parseList(optionalSections(document, EXCLUDE), "$SELECTION.$EXCLUDE"))
    }
}
