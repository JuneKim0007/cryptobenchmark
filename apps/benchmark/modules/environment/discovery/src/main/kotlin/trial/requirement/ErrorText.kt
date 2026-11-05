package io.github.junekim0007.cryptobench.discovery.trial.requirement

// A provider's message can print a key: moduli and encodings go before the cap, or the cap could cut one in half and hide it.
internal object ErrorText {

    const val CAP = 200

    private val KEY_MATERIAL = Regex("""(?:0x)?[0-9a-fA-F]{32,}|\d{32,}|[A-Za-z0-9+/]{48,}={0,2}""")

    private val WHITESPACE = Regex("""\s+""")

    fun of(thrown: Throwable): String = clean(thrown.javaClass.simpleName + ": " + thrown.message.orEmpty())

    fun clean(text: String): String = KEY_MATERIAL.replace(WHITESPACE.replace(text, " "), "<removed>").take(CAP)

    /** Null when the block ran; a provider bug of any kind becomes this one call's text, never an abort. */
    fun refusal(block: () -> Unit): String? = runCatching(block).exceptionOrNull()?.let { of(it) }
}
