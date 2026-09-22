package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.ProviderClassNameWriter
import io.github.junekim0007.cryptobench.discovery.write.TrialDocument
import io.github.junekim0007.cryptobench.discovery.write.TrialYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import java.io.File
import java.security.Provider

class Discovery(
    private val directory: ProbeDirectory,
    private val providerProbe: ProviderProbe = ProviderProbe(),
    private val trialRunner: TrialRunner = TrialRunner(),
    private val defaultRunTrial: DefaultRunTrial = DefaultRunTrial(),
    private val codec: YamlCodec = YamlCodec(),
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

    fun reusable(runtime: RuntimeInfo = RuntimeInfo.unknown()): ReusedRun? {
        val captureFile = directory.newest("probe") ?: return null
        val capture = runCatching { CaptureDocument.parse(codec.load(captureFile.readText())) }.getOrNull() ?: return null
        if (capture.runtime != runtime) {
            return null
        }
        val classesFile = directory.named("probe_classes", captureFile)
        val trialFile = directory.named("trial", captureFile)
        if (!classesFile.isFile || !trialFile.isFile) {
            return null
        }
        val trial = runCatching { TrialDocument.parse(codec.load(trialFile.readText())) }.getOrNull() ?: return null
        return if (trial.capturedAtMillis == capture.capturedAtMillis) ReusedRun(capture, captureFile, classesFile, trialFile) else null
    }

    fun trial(capture: CapturedEnvironment, providers: Array<Provider>?): File =
        trialWriter.write(defaultRunTrial.run(trialRunner.run(capture, providers), providers))
}
