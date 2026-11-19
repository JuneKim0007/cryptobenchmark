package io.github.junekim0007.cryptobench.document

/** The one refusal every versioned document's reader gives. */
object SchemaVersion {
    const val FIELD = "schemaVersion"

    fun require(document: Map<String, *>, reads: Int, name: String) {
        val found = document[FIELD]
        val version = (found as? Number)?.toInt() ?: throw IllegalArgumentException("missing_field: $name: $FIELD")
        require(version == reads) { "unsupported_schema_version: $name: $found, this build reads $reads" }
    }
}
