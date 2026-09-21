package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.TrialReport
import java.io.File

class TrialYamlWriter(
    private val directory: ProbeDirectory,
    private val codec: YamlCodec = YamlCodec(),
) {

    fun toDocument(report: TrialReport): Map<String, Any> = TrialDocument.of(report)

    fun toYaml(report: TrialReport): String = codec.dump(toDocument(report))

    fun fileName(capturedAtMillis: Long): String = ProbeFileName.of("trial", capturedAtMillis)

    fun write(report: TrialReport): File =
        directory.create(fileName(report.capturedAtMillis), toYaml(report))
}
