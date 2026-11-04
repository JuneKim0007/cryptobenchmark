package io.github.junekim0007.cryptobench

import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterialGenerator
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyPlanner
import io.github.junekim0007.cryptobench.preparation.key.plan.KeyRecipe
import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import java.io.File
import java.security.KeyFactory
import java.security.KeyPair
import java.security.NoSuchAlgorithmException
import java.security.spec.PKCS8EncodedKeySpec
import java.security.spec.X509EncodedKeySpec

/** Key pairs for generated scopes: from the key planner once per run and kept on the device; each side decodes the same bytes through its own provider. */
object ScopeKeys {
    // Paired with apps/benchmark-runner/device/adb.py SCOPE_KEYS; ScopedInterop's run starts without it.
    const val FOLDER = "scope-keys"

    private val pairs = HashMap<String, KeyPair>()

    fun pair(type: String, algorithm: String, provider: String, bits: Int, decoder: String): KeyPair =
        pairs.getOrPut("$type|$algorithm|$provider|$bits|$decoder") { kept(recipe(type, algorithm, provider, bits), decoder) }

    // Any operation of the pair shape: the planner names the key algorithm from the type and the name.
    private fun recipe(type: String, algorithm: String, provider: String, bits: Int): KeyRecipe.Pair =
        when (val plan = KeyPlanner(DevicePlan.capability).plan(BenchmarkCase(type, algorithm, provider, Operation.SIGN, keySize = bits))) {
            is KeyRecipe.Pair -> plan
            else -> throw IllegalStateException("no_key_pair: $type $algorithm $provider: ${plan.kind}")
        }

    private fun kept(recipe: KeyRecipe.Pair, decoder: String): KeyPair {
        val folder = File(DevicePlan.directory, FOLDER).also(File::mkdirs)
        val public = File(folder, "${recipe.algorithm}-${recipe.keySize}-${recipe.provider}.public")
        val private = File(folder, "${recipe.algorithm}-${recipe.keySize}-${recipe.provider}.private")
        if (!public.isFile || !private.isFile) {
            val made = (KeyMaterialGenerator().generate(recipe) as KeyMaterial.Pairs).pairs.single()
            public.writeBytes(made.public.encoded)
            private.writeBytes(made.private.encoded)
        }
        val factory = factory(recipe.algorithm, decoder)
        return KeyPair(factory.generatePublic(X509EncodedKeySpec(public.readBytes())), factory.generatePrivate(PKCS8EncodedKeySpec(private.readBytes())))
    }

    private fun factory(algorithm: String, decoder: String): KeyFactory = try {
        KeyFactory.getInstance(algorithm, decoder)
    } catch (absent: NoSuchAlgorithmException) {
        KeyFactory.getInstance(algorithm)
    }
}
