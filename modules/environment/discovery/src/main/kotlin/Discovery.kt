package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.ProviderClassNameWriter
import io.github.junekim0007.cryptobench.discovery.write.TrialYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import java.io.File
import java.security.Provider

/** The module's entry point: wires the probe, the trial and the writers over one output directory. */
class Discovery(
    directory: ProbeDirectory,
    private val providerProbe: ProviderProbe = ProviderProbe(),
    private val trialRunner: TrialRunner = TrialRunner(),
    private val defaultRunTrial: DefaultRunTrial = DefaultRunTrial(),
    codec: YamlCodec = YamlCodec(),
) {

    private val captureWriter = EnvironmentYamlWriter(directory, codec)

    private val classNameWriter = ProviderClassNameWriter(directory, codec)

    private val trialWriter = TrialYamlWriter(directory, codec)

    fun probe(
        providers: Array<Provider>?,
        runtime: RuntimeInfo = RuntimeInfo.unknown(),
        capturedAtMillis: Long = System.currentTimeMillis(),
    ): DiscoveryRun {
        val capture = providerProbe.capture(providers, runtime, capturedAtMillis)
        return DiscoveryRun(
            capture = capture,
            captureFile = captureWriter.write(capture),
            classesFile = classNameWriter.write(capture),
        )
    }

    /** Instantiates every service, then calls every one that instantiated once with a default key. */
    fun trial(capture: CapturedEnvironment, providers: Array<Provider>?): File =
        trialWriter.write(defaultRunTrial.run(trialRunner.run(capture, providers), providers))
}
