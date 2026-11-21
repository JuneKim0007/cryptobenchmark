package io.github.junekim0007.cryptobench.document.versioned

// for a writer that builds its map; a reader parses in its own DocumentReader, so VersionedFile names the file in its refusals
class MapDocument(override val schemaVersion: Int) : DocumentHandler<Map<String, Any>> {

    override fun parse(document: Map<String, Any>): Map<String, Any> = document

    override fun of(value: Map<String, Any>): Map<String, Any> = value
}
