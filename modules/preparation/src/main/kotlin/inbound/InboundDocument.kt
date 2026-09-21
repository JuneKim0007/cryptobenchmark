package io.github.junekim0007.cryptobench.preparation.inbound

class InboundDocument internal constructor(
    val fileName: String,
    internal val run: Map<String, Any>,
    internal val policy: Map<String, Any>,
    internal val providers: Map<String, Any>,
)
