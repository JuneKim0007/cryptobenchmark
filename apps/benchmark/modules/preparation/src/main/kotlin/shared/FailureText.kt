package io.github.junekim0007.cryptobench.preparation.shared

/** A failure as one line a record can keep: class and message, with object identity hashes (Type@1a2b3c4d) dropped; they change per run and JVM. */
object FailureText {

    private val IDENTITY = Regex("@[0-9a-f]{4,}\\b")

    fun of(failure: Throwable): String = stable("${failure.javaClass.simpleName}: ${failure.message}")

    fun stable(text: String): String = text.replace(IDENTITY, "")
}
