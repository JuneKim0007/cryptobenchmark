import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.preparation.parameter.resolve.ResolvedParameters
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.security.Security

class ProviderChoseContractTest {

    // A value the provider fills in identically on every init: discovery names it, preparation drops it as not an IV.
    private val discoveryOnly = setOf("fixedValueBytes")

    @Test
    fun discoveryNamesWhatItChoseWithPreparationsResolvedParameterKeys() {
        val providers = Security.getProviders()
        val report = DefaultRunTrial().run(TrialRunner().run(ProviderProbe().capture(providers), providers), providers)
        val chosen = report.services
            .flatMap { service -> listOf(service.defaultRun) + service.transformations.map { it.defaultRun } }
            .mapNotNull { it?.providerChose?.takeIf(String::isNotBlank) }
        assertTrue("this JVM's trial records no providerChose", chosen.isNotEmpty())
        val keys = chosen.flatMap { line -> line.split(' ').map { it.substringBefore('=') } }.toSortedSet()
        assertEquals(emptySet<String>(), keys - ResolvedParameters.KEYS.toSet() - discoveryOnly)
    }
}
