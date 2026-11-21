package io.github.junekim0007.cryptobench.files

import java.io.File

/** The repository found above the working directory, and the files in it that module tests read: tests/contracts/, the module examples, the committed config, Python's settings defaults.yaml. */
object RepositoryFiles {
    val root: File = generateSequence(File("").absoluteFile) { it.parentFile }
        .firstOrNull { File(it, "${Folders.TESTS}/${Folders.CONTRACTS}/${Folders.CONTRACT_DOCUMENTS}").isDirectory }
        ?: error("${Folders.TESTS}/${Folders.CONTRACTS}/ not found above ${File("").absoluteFile}")
    val contracts = File(root, "${Folders.TESTS}/${Folders.CONTRACTS}")
    val documents = File(contracts, Folders.CONTRACT_DOCUMENTS)
    val yamlCodec = File(contracts, Folders.CONTRACT_YAML_CODEC)
    val runner = File(contracts, Folders.CONTRACT_RUNNER)
    val benchmarkConfig = File(root, "${Folders.CONFIG}/${Folders.BENCHMARK_CONFIG}")
    val defaults = File(root, "lib/cryptobench/cryptobench/shared/settings/defaults.yaml")

    fun example(module: String, name: String): File = File(root, "apps/benchmark/modules/$module/${Folders.EXAMPLE}/$name")
}
