package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.record.PreparedFile
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import java.io.File

/** The swapped calls alone: each callsite.yaml case prepared from its own effective file, as the benchmark prepares any case. */
object CallSitePlan {
    // Paired with scripts/scope/call_site.py PLAN and scripts/device/adb.py CALL_SITE_VERDICTS.
    const val FILE = "callsite.yaml"
    const val VERDICTS = "callsite-verdicts.yaml"

    class Entry(val id: String, val effective: String, val folder: String, val type: String, val algorithm: String,
                val provider: String, val operation: String, val keySize: Int?, val inputSize: Int?, val variant: String)

    sealed interface Outcome {
        class Prepared(val case: PreparedCase) : Outcome
        class NotPrepared(val reason: String) : Outcome
    }

    val entries: List<Entry> by lazy { read(File(DevicePlan.directory, FILE)) }

    fun variants(): List<Array<Any>> = entries.map { entry ->
        arrayOf<Any>(entry.id, { -> Invocations.of(prepared(entry)).perIteration })
    }

    fun outcome(entry: Entry): Outcome = try {
        Outcome.Prepared(prepared(entry))
    } catch (failed: RuntimeException) {
        Outcome.NotPrepared(failed.message ?: failed.javaClass.simpleName)
    }

    private fun prepared(entry: Entry): PreparedCase {
        val cases = preparedIn(entry.effective, entry.folder)
        return cases.firstOrNull { matches(entry, it) }
            ?: throw IllegalStateException("not_prepared: no prepared case is ${entry.type} ${entry.algorithm} ${entry.provider} ${entry.operation} ${entry.variant}; see ${entry.folder}/${SkipFile.NAME}")
    }

    private val prepared = HashMap<String, List<PreparedCase>>()

    private fun preparedIn(effective: String, folder: String): List<PreparedCase> = prepared.getOrPut(effective) {
        val directory = File(DevicePlan.directory, folder)
        Preparation(DevicePlan.capability, SkipFile(directory), PreparedFile(directory)).prepare(File(DevicePlan.directory, effective)).cases
    }

    private fun matches(entry: Entry, prepared: PreparedCase): Boolean {
        val case = prepared.case
        return case.type == entry.type && case.algorithm.equals(entry.algorithm, ignoreCase = true) && case.provider == entry.provider &&
            case.operation.name == entry.operation && case.variant.label == entry.variant &&
            (entry.keySize == null || case.keySize == entry.keySize) && (entry.inputSize == null || case.inputSize == entry.inputSize)
    }

    fun writeVerdicts() {
        val lines = entries.joinToString("") { entry ->
            when (val found = outcome(entry)) {
                is Outcome.Prepared -> "${quoted(entry.id)}: {status: prepared, folder: ${quoted(entry.folder)}, case: ${quoted(found.case.case.id)}}\n"
                is Outcome.NotPrepared -> "${quoted(entry.id)}: {status: not_prepared, reason: ${quoted(found.reason)}}\n"
            }
        }
        File(DevicePlan.directory, VERDICTS).writeText(lines)
    }

    @Suppress("UNCHECKED_CAST")
    private fun read(file: File): List<Entry> {
        if (!file.isFile) return emptyList()
        val document = YamlCodec().load(file.readText())
        return (document["cases"] as? List<Map<String, Any?>> ?: emptyList()).map { c ->
            Entry(c["id"].toString(), c["effective"].toString(), c["folder"].toString(), c["type"].toString(), c["algorithm"].toString(),
                c["provider"].toString(), c["operation"].toString(), (c["keySize"] as? Number)?.toInt(), (c["inputSize"] as? Number)?.toInt(),
                c["variant"].toString())
        }
    }

    private fun quoted(text: String): String =
        "\"" + text.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n") + "\""
}
