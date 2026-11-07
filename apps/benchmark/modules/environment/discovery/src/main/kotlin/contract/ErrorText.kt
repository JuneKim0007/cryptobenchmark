package io.github.junekim0007.cryptobench.discovery.contract

// A provider's message can print a key: encodings go before the cap, or the cap could cut one in half and hide it. Preparation keeps a copy (shared/ErrorText).
internal object ErrorText {

    const val CAP = 200

    private const val REMOVED = "<removed>"

    private val WHITESPACE = Regex("""\s+""")

    private val SEPARATED_BYTES = Regex("""\b(?:0x)?[0-9a-fA-F]{2}(?:(?:\s?[,:-]\s?|\s)(?:0x)?[0-9a-fA-F]{2}\b){7,}""")

    private val NUMBER_LIST = Regex("""\[?-?\d{1,3}(?:,\s?-?\d{1,3}){7,}\]?""")

    // A URL up to its first +, = or ? stays out of the token pass (a lone /+/ segment is kept); a span glued to a '+' is not a URL here.
    private val URL_OR_TOKEN = Regex("""(https?://(?:[\w.~%#@:/-]|(?<=/)\+(?=/))++)(?![\w+/-])|(?<![\w+/-])[\w+/-]{16,}={0,2}(?![\w+/=-])""")

    private val TAIL = Regex("""$REMOVED(?: (?=[\w+/=-]*[0-9+/=])(?:(?=[\w+/=-]*[A-Za-z])[\w+/=-]+|[\w+/=-]{6,})(?![\w+/=-])| $REMOVED)+""")

    private val WORD = Regex("""[A-Z]?[a-z]+""")

    private val VOWEL = Regex("""[aeiouyAEIOUY]""")

    private val DIGIT_THEN_LOWER = Regex("""[0-9][a-z]|[a-z][0-9][A-Za-z]""")

    private val VARIANT_SUFFIX = Regex("""(?<=[0-9])[a-z](?=$|[-_/0-9])""")

    private val HEX = Regex("""[0-9a-fA-F]*[a-fA-F][0-9a-fA-F]*""")

    private val DECIMAL = Regex("""\d{32,}""")

    fun of(thrown: Throwable, context: String = ""): String = clean(context + thrown.javaClass.simpleName + ": " + thrown.message.orEmpty())

    fun clean(text: String): String {
        val bytes = NUMBER_LIST.replace(SEPARATED_BYTES.replace(WHITESPACE.replace(text, " "), REMOVED), REMOVED)
        val tokens = URL_OR_TOKEN.replace(bytes) { if (it.groups[1] != null || isName(it.value)) it.value else REMOVED }
        return TAIL.replace(tokens, REMOVED).take(CAP)
    }

    /** Null when the block ran; a provider bug of any kind becomes this one call's text, never an abort. */
    fun refusal(block: () -> Unit): String? = Attempt.of(block).exceptionOrNull()?.let { of(it) }

    // A name reads as words, acronyms and numbers with at most one oddity (a vowelless or two-letter word, a digit before lowercase); an encoding has more, or '+', padding, only hex.
    private fun isName(token: String): Boolean {
        if ('+' in token || '=' in token || DECIMAL.containsMatchIn(token) || HEX.matches(token.filter { it !in "-_/" })) return false
        val words = WORD.findAll(VARIANT_SUFFIX.replace(token, "")).map { it.value }.toList()
        if (words.any { it.length < 2 }) return false
        return words.count { !VOWEL.containsMatchIn(it) } + words.count { it.length == 2 } + DIGIT_THEN_LOWER.findAll(token).count() <= 1
    }
}
