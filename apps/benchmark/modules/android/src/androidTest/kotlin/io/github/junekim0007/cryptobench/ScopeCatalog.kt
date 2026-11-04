package io.github.junekim0007.cryptobench

/** The scopes apps/benchmark-runner/scope/generate.py compiled into this test APK. */
interface ScopeCatalog {

    fun scopes(): List<Scope>

    companion object {
        // Paired with apps/benchmark-runner/scope/wrapper.py CATALOG; only a --harness build contains it.
        const val GENERATED = "io.github.junekim0007.cryptobench.scoped.GeneratedScopes"

        // An input that cannot be built fails its own scope's check, not the whole catalog.
        fun guarded(id: String, build: () -> Scope): Scope = try {
            build()
        } catch (failure: RuntimeException) {
            val failed = { throw failure }
            Scope(id, failed, failed, ScopeInterop.SameOutput)
        }

        fun load(): List<Scope> {
            val type = try {
                Class.forName(GENERATED)
            } catch (missing: ClassNotFoundException) {
                throw IllegalStateException("missing_class: $GENERATED; run apps/benchmark-runner/pipeline.py --device --harness <harness.yaml>", missing)
            }
            return (type.getDeclaredConstructor().newInstance() as ScopeCatalog).scopes()
        }
    }
}
