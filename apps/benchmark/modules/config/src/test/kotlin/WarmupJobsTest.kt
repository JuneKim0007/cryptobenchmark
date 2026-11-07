package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.WarmupJobs
import io.github.junekim0007.cryptobench.config.global.dto.Warmup
import io.github.junekim0007.cryptobench.config.testset.dto.Rule
import org.junit.Assert.assertEquals
import org.junit.Test

/** The warm-up selects with the include's rule (names folded, groups honoured); the runner gets the entries, not the rules. */
class WarmupJobsTest {

    private val providers = mapOf(
        "SUN" to mapOf("MessageDigest" to mapOf("SHA-256" to Unit)),
        "SunJCE" to mapOf("Cipher" to mapOf("RSA@oaep" to Unit, "RSA" to Unit)),
    )

    private fun resolve(vararg jobs: Rule) = WarmupJobs.resolve(Warmup(10, jobs.toList()), providers)

    @Test
    fun jobsResolveToTheEntriesTheySelect() {
        val (warmup, warnings) = resolve(Rule(type = "messagedigest", name = "SHA-256"), Rule(name = "RSA", group = "oaep"), Rule(name = "Nothing"))
        assertEquals(Warmup(10, listOf(Rule("SUN", "MessageDigest", "SHA-256"), Rule("SunJCE", "Cipher", "RSA", "oaep"))), warmup)
        assertEquals(listOf("warmup_job_matches_nothing: {name=Nothing}"), warnings)
    }

    @Test
    fun noEntrySelectedTurnsTheWarmupOff() {
        assertEquals(Warmup(0), resolve(Rule(name = "Nothing")).first)
    }

    @Test
    fun noJobsKeepThePlansFirstCases() {
        assertEquals(Warmup(10) to emptyList<String>(), resolve())
    }
}
