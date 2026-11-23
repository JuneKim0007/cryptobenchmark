package io.github.junekim0007.cryptobench.document.catalogue

import io.github.junekim0007.cryptobench.document.DocumentFields
import io.github.junekim0007.cryptobench.document.YamlCodec

/** algorithms/recipes.yaml beside [FamilyCatalogue]: the one recipe an entry's required rows passed to one call name (several refused), and a recipe and those rows at a build to the {class, arguments} tree jca's ParameterBinder binds, as Python's guide_items.parameter_tree; a builder or keyRef recipe, or a role without its value, is [Unbuildable]. */
class Recipes(private val byId: Map<String, Any>) {

    // recipes: the ids a refusal of several names
    class Unbuildable(detail: String, val recipes: List<String> = emptyList()) : IllegalArgumentException("$CODE: $detail")

    fun tree(id: String, entry: FamilyCatalogue.Entry, build: String?): Map<String, Any> = tree(id, rows(entry, build).associateBy { it[NAME] })

    fun one(entry: FamilyCatalogue.Entry, build: String?, passedTo: String): String? {
        val ids = rows(entry, build).filter { it[PASSED_TO] == passedTo }.mapNotNull { it[RECIPE] as? String }.distinct()
        return if (ids.size > 1) throw Unbuildable("$ids are several objects for one $passedTo", ids) else ids.singleOrNull()
    }

    private fun rows(entry: FamilyCatalogue.Entry, build: String?) = (entry.fields(build)[REQUIRED] as? List<*>).orEmpty().filterIsInstance<Map<*, *>>()

    private fun tree(id: String, rows: Map<Any?, Map<*, *>>): Map<String, Any> {
        val recipe = byId[id] as? Map<*, *> ?: throw Unbuildable("$id is no recipe")
        val type = recipe[CLASS] as? String ?: throw Unbuildable("$id is not a constructor")
        return linkedMapOf(CLASS to type, ARGUMENTS to (recipe[ARGS] as? List<*>).orEmpty().map { argument(it as Map<*, *>, rows) })
    }

    private fun argument(argument: Map<*, *>, rows: Map<Any?, Map<*, *>>): Any {
        val role = argument[ROLE]
        val row = rows[role].orEmpty()
        return when (argument[KIND]) {
            CONSTANT -> argument[VALUE] ?: throw Unbuildable("a constant without a value")
            RECIPE -> tree(argument[RECIPE] as String, rows)
            ENUM -> mapOf(FIELD to argument[VALUE])
            KEY_REF -> throw Unbuildable("$role is a key reference")
            BYTES -> "fresh(${row[BYTES]?.takeIf { it != 0 } ?: throw Unbuildable("$role has no length")})"
            else -> argument[VALUE] ?: row[VALUE] ?: throw Unbuildable("$role has no value")
        }
    }

    companion object {

        const val CODE = "guide_recipe_unbuildable"
        private const val REQUIRED = "required"
        private const val NAME = "name"
        private const val PASSED_TO = "passedTo"
        private const val CLASS = "class"
        private const val ARGUMENTS = "arguments"
        private const val ARGS = "args"
        private const val ROLE = "role"
        private const val KIND = "kind"
        private const val VALUE = "value"
        private const val CONSTANT = "constant"
        private const val RECIPE = "recipe"
        private const val ENUM = "enum"
        private const val FIELD = "field"
        private const val KEY_REF = "keyRef"
        private const val BYTES = "bytes"

        val bundled: Recipes by lazy { parse(FamilyCatalogue.resource(FamilyCatalogue.RECIPES)) }

        fun parse(text: String): Recipes = Recipes(DocumentFields.section(YamlCodec.DOCUMENT.load(text), "recipes"))
    }
}
