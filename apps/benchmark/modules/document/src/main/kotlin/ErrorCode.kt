package io.github.junekim0007.cryptobench.document

/** The one Kotlin shape of an error code, the word a `<code>: <detail>` message starts with. */
object ErrorCode {
    val PATTERN = Regex("[a-z][a-z0-9_]*")
}
