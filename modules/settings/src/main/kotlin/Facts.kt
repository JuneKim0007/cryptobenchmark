package io.github.junekim0007.cryptobench.settings

/** What the device can support, from discovery/facts.yaml; a null fact was not gathered. */
data class Facts(
    val gathered: Boolean = false,
    val sdkInt: Int? = null,
    val rooted: Boolean? = null,
    val cores: List<Core>? = null,
    val pinning: Boolean? = null,
) {
    data class Core(val index: Int, val online: Boolean, val maxKhz: Long?)

    /** Why a fact a setting needs is missing. */
    fun unknown(fact: String): String = if (gathered) "facts_unknown: facts.yaml has no $fact" else "facts_unknown: no facts.yaml for this run"

    companion object {
        val UNKNOWN = Facts()

        fun read(document: Map<String, Any?>): Facts {
            require(document["schemaVersion"] == 1) { "unsupported: facts.yaml schemaVersion ${document["schemaVersion"]}" }
            val cores = section(document, "cpu")?.get("cores")?.let { listed ->
                (listed as? List<*> ?: throw wrongType("cpu.cores", "a list")).mapIndexed { i, raw ->
                    val core = raw as? Map<*, *> ?: throw wrongType("cpu.cores[$i]", "a mapping")
                    Core(
                        (core["core"] as? Number)?.toInt() ?: throw wrongType("cpu.cores[$i].core", "a number"),
                        core["online"] as? Boolean ?: throw wrongType("cpu.cores[$i].online", "true or false"),
                        core["maxKhz"]?.let { (it as? Number)?.toLong() ?: throw wrongType("cpu.cores[$i].maxKhz", "a number") },
                    )
                }
            }
            return Facts(
                gathered = true,
                sdkInt = section(document, "os")?.get("sdkInt")?.let { (it as? Number)?.toInt() ?: throw wrongType("os.sdkInt", "a number") },
                rooted = document["rooted"]?.let { it as? Boolean ?: throw wrongType("rooted", "true or false") },
                cores = cores,
                pinning = document["pinning"]?.let { it as? Boolean ?: throw wrongType("pinning", "true or false") },
            )
        }

        private fun section(document: Map<String, Any?>, key: String): Map<*, *>? =
            document[key]?.let { it as? Map<*, *> ?: throw wrongType(key, "a mapping") }

        private fun wrongType(field: String, expected: String) = IllegalArgumentException("wrong_type: facts.yaml $field expects $expected")
    }
}
