package io.github.junekim0007.cryptobench.files

import java.time.Instant
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter

/** Discovery's stamped files: prefix_<UTC stamp>.yaml, and the file of another prefix carrying the same stamp. */
object StampedName {
    const val PROBE = "probe"
    const val TRIAL = "trial"
    const val REQUIREMENTS = "requirements"

    private const val STAMP_DIGITS = """\d{8}T\d{6}Z"""
    private const val SUFFIX = ".yaml"
    private val STAMP: DateTimeFormatter = DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC)
    private val STAMPED = Regex(STAMP_DIGITS + Regex.escape(SUFFIX))
    private val STAMP_IN_NAME = Regex("_($STAMP_DIGITS)" + Regex.escape(SUFFIX) + "$")

    fun of(prefix: String, capturedAtMillis: Long): String = prefix + "_" + STAMP.format(Instant.ofEpochMilli(capturedAtMillis)) + SUFFIX

    fun isStamped(prefix: String, name: String): Boolean = name.startsWith(prefix + "_") && name.removePrefix(prefix + "_").matches(STAMPED)

    fun sibling(prefix: String, stampedName: String): String = prefix + "_" + stampedName.substringAfterLast('_')

    fun stampOf(name: String): String? = STAMP_IN_NAME.find(name)?.groupValues?.get(1)
}
