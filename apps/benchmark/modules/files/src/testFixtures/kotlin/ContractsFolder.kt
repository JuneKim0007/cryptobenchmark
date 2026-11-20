package io.github.junekim0007.cryptobench.files

import java.io.File

/** The repository's tests/contracts/ folder found above the working directory, its subfolders, the module examples and Python's settings defaults.yaml, for the tests that read them. */
object ContractsFolder {
    private val repository: File = generateSequence(File("").absoluteFile) { it.parentFile }
        .firstOrNull { File(it, "${Folders.TESTS}/${Folders.CONTRACTS}/${Folders.CONTRACT_DOCUMENTS}").isDirectory }
        ?: error("${Folders.TESTS}/${Folders.CONTRACTS}/ not found above ${File("").absoluteFile}")
    val root = File(repository, "${Folders.TESTS}/${Folders.CONTRACTS}")
    val documents = File(root, Folders.CONTRACT_DOCUMENTS)
    val yamlCodec = File(root, Folders.CONTRACT_YAML_CODEC)
    val runner = File(root, Folders.CONTRACT_RUNNER)
    val defaults = File(repository, "lib/cryptobench/cryptobench/shared/settings/defaults.yaml")

    fun example(module: String, name: String): File = File(repository, "apps/benchmark/modules/$module/example/$name")
}
