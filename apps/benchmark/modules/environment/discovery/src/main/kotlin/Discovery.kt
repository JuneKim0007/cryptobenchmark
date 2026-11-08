package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.discovery.adapter.DeviceRuntimeReader
import io.github.junekim0007.cryptobench.discovery.adapter.ProviderProbe
import io.github.junekim0007.cryptobench.discovery.bundled.InstalledProvider
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.discovery.contract.CapturedEnvironment
import io.github.junekim0007.cryptobench.discovery.contract.RuntimeInfo
import io.github.junekim0007.cryptobench.discovery.trial.DefaultRunTrial
import io.github.junekim0007.cryptobench.discovery.trial.TrialRunner
import io.github.junekim0007.cryptobench.discovery.trial.call.DefaultKeys
import io.github.junekim0007.cryptobench.discovery.trial.requirement.RequirementTrial
import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.EnvironmentYamlWriter
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.discovery.write.RequirementDocument
import io.github.junekim0007.cryptobench.discovery.write.RequirementYamlWriter
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
    private val requirementTrial: RequirementTrial = RequirementTrial(),
    private val codec: YamlCodec = YamlCodec(),
) {

    private val captureWriter = EnvironmentYamlWriter(directory, codec)

    private val trialWriter = TrialYamlWriter(directory, codec)

    private val requirementWriter = RequirementYamlWriter(directory, codec)

    fun probe(
        providers: Array<Provider>?,
        runtime: RuntimeInfo = DeviceRuntimeReader.read(),
        capturedAtMillis: Long = System.currentTimeMillis(),
        bundled: List<InstalledProvider> = emptyList(),
    ): DiscoveryRun {
        val capture = providerProbe.capture(providers, runtime, capturedAtMillis, bundled)
        return DiscoveryRun(
            capture = capture,
            captureFile = captureWriter.write(capture),
        )
    }

    fun reusable(runtime: RuntimeInfo = DeviceRuntimeReader.read()): ReusedRun? {
        val captureFile = directory.newest("probe") ?: return null
        val capture = Attempt.of { CaptureDocument.parse(codec.load(captureFile.readText())) }.getOrNull() ?: return null
        if (capture.runtime != runtime) {
            return null
        }
        val trialFile = directory.named("trial", captureFile)
        val requirementsFile = directory.named(RequirementYamlWriter.PREFIX, captureFile)
        if (!trialFile.isFile || !requirementsFile.isFile) {
            return null
        }
        val trial = Attempt.of { TrialDocument.parse(codec.load(trialFile.readText())) }.getOrNull() ?: return null
        val requirements = Attempt.of { RequirementDocument.parse(codec.load(requirementsFile.readText())) }.getOrNull() ?: return null
        val sameCapture = trial.capturedAtMillis == capture.capturedAtMillis && requirements.capturedAtMillis == capture.capturedAtMillis
        return if (sameCapture) ReusedRun(capture, captureFile, trialFile, requirementsFile) else null
    }

    fun trial(capture: CapturedEnvironment, providers: Array<Provider>?): TrialFiles {
        val keys = DefaultKeys(providers.orEmpty().toList())
        val trial = defaultRunTrial.run(trialRunner.run(capture, providers), providers, keys)
        return TrialFiles(trialWriter.write(trial), requirementWriter.write(requirementTrial.run(capture, trial, providers, keys)))
    }
}
