import io.github.junekim0007.cryptobench.files.FileNames
import io.github.junekim0007.cryptobench.files.Folders
import java.io.File
import kotlin.system.exitProcess

// Every main's contract: arguments it cannot take are its usage line and exit 2; any Exception is one error line and exit 1, no stack trace.
// An Error is not caught: it ends the JVM as it is (Check's finally still writes its records).
internal fun command(arguments: Array<String>, usage: String, valid: (Array<String>) -> Boolean, block: () -> Unit) {
    if (!valid(arguments)) {
        System.err.println("usage: $usage")
        exitProcess(USAGE)
    }
    try {
        block()
    } catch (error: Exception) {
        System.err.println("error: ${error.message ?: error.javaClass.name}")
        exitProcess(1)
    }
}

const val USAGE = 2

internal fun committedGlobal(): File? =
    generateSequence(File("").absoluteFile) { it.parentFile }.map { File(File(it, Folders.CONFIG), FileNames.GLOBAL) }.firstOrNull { it.exists() }
