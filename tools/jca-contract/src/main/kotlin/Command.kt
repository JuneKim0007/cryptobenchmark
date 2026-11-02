import java.io.File
import kotlin.system.exitProcess

internal fun fail(error: Exception): Nothing {
    System.err.println("error: ${error.message}")
    exitProcess(1)
}

internal fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "config/global.yaml") }.firstOrNull { it.exists() }
