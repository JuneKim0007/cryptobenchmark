package io.github.junekim0007.cryptobench.files

import java.io.File

/** The repository's contracts/ folder found above the working directory, and its subfolders, for the tests that read them. */
object ContractsFolder {
    val root: File = generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, Folders.CONTRACTS) }
        .firstOrNull { File(it, Folders.CONTRACT_DOCUMENTS).isDirectory } ?: error("${Folders.CONTRACTS}/ not found above ${File("").absoluteFile}")
    val defaults = File(root, Folders.CONTRACT_DEFAULTS)
    val documents = File(root, Folders.CONTRACT_DOCUMENTS)
    val yamlCodec = File(root, Folders.CONTRACT_YAML_CODEC)
    val runner = File(root, Folders.CONTRACT_RUNNER)
}
