package io.github.junekim0007.cryptobench.preparation.shared

/** A failure as one line a record can keep: key encodings removed within the cap ([ErrorText]), object identity hashes (Type@1a2b3c4d) dropped; they change per run and JVM. */
object FailureText {

    private val IDENTITY = Regex("@[0-9a-f]{4,}\\b")

    fun of(failure: Throwable, context: String = ""): String = stable(ErrorText.of(failure, context))

    fun stable(text: String): String = text.replace(IDENTITY, "")
}
