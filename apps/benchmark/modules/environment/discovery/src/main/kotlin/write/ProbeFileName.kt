package io.github.junekim0007.cryptobench.discovery.write

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

internal object ProbeFileName {

    private val STAMP: DateTimeFormatter =
        DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)

    private val STAMPED = Regex("""\d{8}T\d{6}Z\.yaml""")

    fun of(prefix: String, capturedAtMillis: Long): String =
        prefix + "_" + STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + ".yaml"

    fun isStamped(prefix: String, name: String): Boolean =
        name.startsWith(prefix + "_") && name.removePrefix(prefix + "_").matches(STAMPED)

    fun sibling(prefix: String, stampedName: String): String =
        prefix + "_" + stampedName.substringAfterLast('_')
}
