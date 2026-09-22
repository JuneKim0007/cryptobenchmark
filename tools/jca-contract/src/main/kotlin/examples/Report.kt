package examples

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.query.CaptureQuery
import io.github.junekim0007.cryptobench.discovery.query.TrialQuery
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import java.security.Security

/**
 * What this JVM can do, asked through CaptureQuery and TrialQuery.
 * `./gradlew run -PmainClass=examples.ReportKt --args="Cipher AES SunJCE"`
 */
fun main(arguments: Array<String>) {
    val type = arguments.getOrNull(0) ?: "Cipher"
    val algorithm = arguments.getOrNull(1) ?: "AES"
    val provider = arguments.getOrNull(2) ?: "SunJCE"

    val providers = Security.getProviders()
    val capture = ProviderProbe().capture(providers)
    val captureQuery = CaptureQuery(capture)
    val trialQuery = TrialQuery(TrialRunner().run(capture, providers))

    println("## who serves $type/$algorithm")
    for (serving in captureQuery.whoServes(type, algorithm)) {
        val service = captureQuery.serviceOf(serving.name, type, algorithm) ?: continue
        val trialled = trialQuery.serviceTrial(serving.name, type, service.algorithm)
        println("${serving.precedence}. ${serving.name}: ${trialled?.outcome?.let { if (it.instantiates) "starts" else it.error } ?: "not tried"}")
    }
    println("known as: ${captureQuery.namesOf(type, algorithm).joinToString(", ")}")

    val transformation = "$algorithm/GCM/NoPadding"
    println("\n## $provider $transformation")
    val registered = captureQuery.serviceOf(provider, type, transformation)
    val outcome = if (registered != null) {
        trialQuery.serviceTrial(provider, type, registered.algorithm)?.outcome
    } else {
        trialQuery.transformationTrial(provider, algorithm, transformation)?.outcome
    }
    println("registered as its own service: ${registered != null}")
    println(outcome?.let { if (it.instantiates) "starts" else it.error } ?: "not tried")

    println("\n## services that start, per provider")
    for ((name, counts) in trialQuery.instantiationByProvider()) {
        println("$name: ${counts.first}/${counts.second}")
    }

    println("\n## what the JCA refuses")
    for (service in trialQuery.failingServices()) {
        println("$service")
    }
    for (failure in trialQuery.failingTransformations().take(5)) {
        println("${failure.provider} ${failure.transformation}: ${failure.error}")
    }

    println("\n## only on $provider")
    for (service in captureQuery.onlyOn(provider).take(10)) {
        println("${service.type}.${service.algorithm}")
    }
}
