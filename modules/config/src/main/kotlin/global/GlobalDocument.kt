package io.github.junekim0007.cryptobench.config.global

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

/**
 * global.yaml. Each section has one owner and one parser, listed in SECTIONS; a section nobody owns is an error,
 * so a misspelt `rn:` fails instead of silently running with defaults.
 */
object GlobalDocument : DocumentHandler<GlobalConfig> {

    override val schemaVersion: Int = 1

    const val SELECTION = "selection"
    const val RUN = "run"
    const val POLICY = "policy"

    private const val TEST_SET = "testSet"
    private const val EXCLUDE = "exclude"

    val SECTIONS: List<String> = listOf(SELECTION, RUN, POLICY)

    override fun of(value: GlobalConfig): Map<String, Any> = linkedMapOf(
        SELECTION to linkedMapOf(TEST_SET to value.selection.testSet, EXCLUDE to value.selection.exclude.map { RuleDocument.of(it) }),
        RUN to RunDocument.of(value.run),
        POLICY to PolicyDocument.of(value.policy),
    )

    override fun parse(document: Map<String, Any>): GlobalConfig {
        val unknown = document.keys.filter { it != "schemaVersion" && it !in SECTIONS }
        require(unknown.isEmpty()) { "unknown_section: $unknown, known $SECTIONS" }
        return GlobalConfig(
            selection = selection(section(document, SELECTION)),
            run = optionalSection(document, RUN)?.let { RunDocument.parse(it, RUN) } ?: RunSettings(),
            policy = optionalSection(document, POLICY)?.let { PolicyDocument.parse(it, POLICY) } ?: Policy(),
        )
    }

    private fun selection(document: Map<String, Any>): Selection {
        expectKeys(document, listOf(TEST_SET, EXCLUDE), SELECTION)
        return Selection(string(document, TEST_SET), RuleDocument.parseList(optionalSections(document, EXCLUDE), "$SELECTION.$EXCLUDE"))
    }
}
