package io.github.junekim0007.cryptobench.discovery.adapter

internal object AttributeValueParser {

    private fun parse(attribute: String, raw: String): Any = when (AttributeKind.of(attribute)) {
        AttributeKind.LIST -> splitPipe(raw)
        AttributeKind.INT -> raw.trim().toInt()
        AttributeKind.BOOL -> raw.trim().toBoolean()
        AttributeKind.STRING -> raw
    }

    fun parseOrRaw(attribute: String, raw: String): Any = try {
        parse(attribute, raw)
    } catch (e: NumberFormatException) {
        raw
    }

    private fun splitPipe(raw: String): List<String> =
        raw.split('|').map { it.trim() }.filter { it.isNotEmpty() }
}
