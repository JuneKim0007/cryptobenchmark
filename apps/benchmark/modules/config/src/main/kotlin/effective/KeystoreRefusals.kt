package io.github.junekim0007.cryptobench.config.effective

import io.github.junekim0007.cryptobench.config.effective.dto.EffectiveEntry
import io.github.junekim0007.cryptobench.config.entry.KeySource
import io.github.junekim0007.cryptobench.config.inventory.dto.Inventory
import io.github.junekim0007.cryptobench.config.names.AlgorithmNames

/** A secure entry against the keystore trial: the key sizes it keeps, and the trial's coded refusal of each row it refused. A row the trial lacks keeps its size. */
object KeystoreRefusals {

    data class Checked(val keySizes: List<Int>, val refusals: List<String>, val whole: Boolean)

    private const val CURVE_SPEC = "java.security.spec.ECGenParameterSpec"
    private const val CLASS = "class"
    private const val ARGUMENTS = "arguments"
    private const val TEE = "tee"

    fun of(entry: EffectiveEntry, located: Inventory.Located, inventory: Inventory): Checked {
        val backing = entry.key[KeySource.BACKING] as? String ?: TEE
        val rows = inventory.keystore.filter {
            it.provider == located.provider && it.backing == backing &&
                AlgorithmNames.fold(it.type) == AlgorithmNames.fold(located.type) && AlgorithmNames.fold(it.algorithm) == AlgorithmNames.fold(located.name)
        }
        if (entry.keySizes.isNotEmpty()) {
            val refused = entry.keySizes.mapNotNull { size -> rows.firstOrNull { it.keySize == size && it.curve.isEmpty() }?.takeIf { !it.supported }?.let { size to it.error } }
            val kept = entry.keySizes - refused.map { it.first }.toSet()
            return Checked(kept, refused.map { it.second }, kept.isEmpty())
        }
        val curve = curveOf(entry.key)
        val refused = rows.firstOrNull { it.keySize == null && AlgorithmNames.fold(it.curve) == AlgorithmNames.fold(curve) }?.takeIf { !it.supported }
        return Checked(entry.keySizes, listOfNotNull(refused?.error), refused != null)
    }

    // the curve an entry's key spec names, "" without one
    private fun curveOf(key: Map<String, Any>): String {
        if (key[CLASS] != CURVE_SPEC) return ""
        return ((key[ARGUMENTS] as? List<*>)?.singleOrNull() as? String).orEmpty()
    }
}
