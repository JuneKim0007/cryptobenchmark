package io.github.junekim0007.cryptobench.preparation.engine

import io.github.junekim0007.cryptobench.preparation.measurement.BenchmarkCase
import java.security.Signature
import javax.crypto.Cipher

internal object CaseEngines {

    fun cipher(case: BenchmarkCase): Cipher = Cipher.getInstance(case.algorithm, case.provider)

    fun signature(case: BenchmarkCase): Signature = Signature.getInstance(case.algorithm, case.provider)
}
