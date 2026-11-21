package io.github.junekim0007.cryptobench.document.versioned

/** A reader's `<code>: <rest>` refusal with the file it read put after the code: `<code>: <file>: <rest>`. */
object FileRefusal {

    private const val SEPARATOR = ": "

    fun of(fileName: String, message: String): String {
        val code = message.substringBefore(SEPARATOR)
        return "$code$SEPARATOR$fileName${message.substring(code.length)}"
    }
}
