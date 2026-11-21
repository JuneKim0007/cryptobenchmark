package io.github.junekim0007.cryptobench.document.versioned

// the caller parses the map itself, so its refusals carry no file-name prefix
class MapDocument(override val schemaVersion: Int) : DocumentHandler<Map<String, Any>> {

    override fun parse(document: Map<String, Any>): Map<String, Any> = document

    override fun of(value: Map<String, Any>): Map<String, Any> = value
}
