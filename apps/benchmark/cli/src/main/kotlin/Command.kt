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
