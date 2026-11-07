package io.github.junekim0007.cryptobench.preparation.operation

// An engine's init, told which call it is; a fun interface keeps the Int primitive where (E, Int) -> Unit boxes it per call.
internal fun interface EngineInit<E> {
    fun init(engine: E, call: Int)
}
