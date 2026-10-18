package io.github.junekim0007.cryptobench.settings

/** What the device can support, from facts.yaml; null means the fact was not gathered (a host run, an old run). */
data class Facts(
    val sdkInt: Int? = null,
    val rooted: Boolean? = null,
    val cores: List<Core>? = null,
    val pinning: Boolean? = null,
) {
    data class Core(val index: Int, val online: Boolean, val maxKhz: Long?)

    companion object {
        val UNKNOWN = Facts()

        fun read(document: Map<String, Any?>): Facts {
            require(document["schemaVersion"] == 1) { "unsupported: facts.yaml schemaVersion ${document["schemaVersion"]}" }
            fun section(key: String) = document[key] as? Map<*, *>
            val cores = (section("cpu")?.get("cores") as? List<*>)?.map { raw ->
                val core = raw as? Map<*, *> ?: throw IllegalArgumentException("wrong_type: facts.yaml cpu.cores entry")
                Core((core["core"] as Number).toInt(), core["online"] == true, (core["maxKhz"] as? Number)?.toLong())
            }
            return Facts((section("os")?.get("sdkInt") as? Number)?.toInt(), document["rooted"] as? Boolean, cores, document["pinning"] as? Boolean)
        }
    }
}
