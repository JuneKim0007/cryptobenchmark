package io.github.junekim0007.cryptobench

/** The scopes scripts/scope/generate.py compiled into this test APK. */
interface ScopeCatalog {

    fun scopes(): List<Scope>

    companion object {
        // Paired with scripts/scope/wrapper.py CATALOG; only a --harness build contains it.
        const val GENERATED = "io.github.junekim0007.cryptobench.scoped.GeneratedScopes"

        fun load(): List<Scope> {
            val type = try {
                Class.forName(GENERATED)
            } catch (missing: ClassNotFoundException) {
                throw IllegalStateException("missing_class: $GENERATED; run scripts/pipeline.py --device --harness <harness.yaml>", missing)
            }
            return (type.getDeclaredConstructor().newInstance() as ScopeCatalog).scopes()
        }
    }
}
