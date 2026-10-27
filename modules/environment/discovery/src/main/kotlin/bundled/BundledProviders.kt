package io.github.junekim0007.cryptobench.discovery.bundled

object BundledProviders {

    const val KEY = "bundledProviders"

    private const val ARTIFACT = "artifact"
    private const val CREATE = "create"
    private const val ALIAS = "alias"

    fun read(document: Map<String, Any>): List<BundledProvider> {
        val entries = document[KEY] ?: return emptyList()
        val list = entries as? List<*> ?: throw BundledProviderException("wrong_type", KEY)
        return list.map { entry ->
            val fields = entry as? Map<*, *> ?: throw BundledProviderException("wrong_type", KEY)
            val unknown = fields.keys.filter { it !in listOf(ARTIFACT, CREATE, ALIAS) }
            if (unknown.isNotEmpty()) throw BundledProviderException("unknown_keys", "$KEY $unknown")
            val alias = fields[ALIAS]?.let { it as? String ?: throw BundledProviderException("wrong_type", "$KEY.$ALIAS") }
            BundledProvider(text(fields, ARTIFACT), text(fields, CREATE), alias)
        }
    }

    private fun text(fields: Map<*, *>, key: String): String =
        fields[key] as? String ?: throw BundledProviderException("missing_field", "$KEY.$key")
}
