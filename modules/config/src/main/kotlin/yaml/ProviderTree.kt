package io.github.junekim0007.cryptobench.config.yaml

import io.github.junekim0007.cryptobench.config.yaml.DocumentFields.asSection

object ProviderTree {

    fun <T> of(tree: Map<String, Map<String, Map<String, T>>>, entry: (T) -> Map<String, Any>): Map<String, Any> =
        tree.mapValuesTo(LinkedHashMap()) { (_, types) ->
            types.mapValuesTo(LinkedHashMap()) { (_, entries) -> entries.mapValuesTo(LinkedHashMap()) { (_, value) -> entry(value) } }
        }

    fun <T> parse(document: Map<String, Any>, path: String, entry: (Map<String, Any>) -> T): Map<String, Map<String, Map<String, T>>> =
        document.mapValuesTo(LinkedHashMap()) { (provider, types) ->
            asSection(types, "$path.$provider").mapValuesTo(LinkedHashMap()) { (type, entries) ->
                asSection(entries, "$path.$provider.$type").mapValuesTo(LinkedHashMap()) { (name, value) ->
                    entry(asSection(value, "$path.$provider.$type.$name"))
                }
            }
        }
}
