package io.github.junekim0007.cryptobench.document.versioned

import io.github.junekim0007.cryptobench.document.ErrorCode

/** A reader's `<code>: <rest>` refusal with the file it read put after the code: `<code>: <file>: <rest>`. */
object FileRefusal {

    private const val SEPARATOR = ": "

    fun of(fileName: String, message: String): String {
        val code = message.substringBefore(SEPARATOR)
        if (!ErrorCode.PATTERN.matches(code)) return "invalid: refusal without a code: $fileName: $message"
        return "$code$SEPARATOR$fileName${message.substring(code.length)}"
    }
}
