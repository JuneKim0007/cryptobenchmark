import java.io.File
import kotlin.system.exitProcess

internal fun fail(error: Exception): Nothing {
    System.err.println("error: ${error.message}")
    exitProcess(1)
}

// A command's coded failure as one error line and exit 1; an Error is not caught here and ends the JVM as it is.
internal fun command(block: () -> Unit) = try {
    block()
} catch (error: Exception) {
    fail(error)
}

internal fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(it, "config/global.yaml") }.firstOrNull { it.exists() }
