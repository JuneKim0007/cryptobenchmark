package io.github.junekim0007.cryptobench.discovery.write

import io.github.junekim0007.cryptobench.discovery.contract.RequirementReport
import java.io.File

class RequirementYamlWriter(
    private val directory: ProbeDirectory,
    private val codec: YamlCodec = YamlCodec(),
) {

    // One service at a time: SnakeYAML holds a node per value of what it is given, and an API 26 heap is 48 MB.
    fun write(report: RequirementReport): File =
        directory.create(ProbeFileName.of(PREFIX, report.capturedAtMillis)) { out ->
            codec.dump(RequirementDocument.header(report), out)
            if (report.services.isEmpty()) {
                codec.dump(mapOf(RequirementDocument.SERVICES to emptyList<Any>()), out)
            } else {
                out.write(RequirementDocument.SERVICES + ":\n")
                report.services.forEach { codec.dump(listOf(RequirementDocument.serviceDocument(it)), out) }
            }
        }

    companion object {
        const val PREFIX = "requirements"
    }
}
