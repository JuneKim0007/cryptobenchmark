package io.github.junekim0007.cryptobench.preparation.peer

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

/** A call a consumer judges: the case as prepared, the engine it read back and what it returned. */
class ProducedCall(val prepared: PreparedCase, val engine: Any?, val output: Any?)
