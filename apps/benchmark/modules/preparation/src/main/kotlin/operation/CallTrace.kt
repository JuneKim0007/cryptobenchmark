package io.github.junekim0007.cryptobench.preparation.operation

/** The engine an EngineCall holds and how many inits it has run; read before and after a call to see what it redid. */
class CallTrace(val engine: Any, val inits: Int)
