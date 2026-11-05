package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import java.io.File

class RequirementYamlWriter(
    private val directory: ProbeDirectory,
    private val codec: YamlCodec = YamlCodec(),
) {

    fun write(report: RequirementReport): File =
        directory.create(ProbeFileName.of(PREFIX, report.capturedAtMillis), codec.dump(RequirementDocument.of(report)))

    companion object {
        const val PREFIX = "requirements"
    }
}
