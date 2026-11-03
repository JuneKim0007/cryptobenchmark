package io.github.junekim0007.cryptobench.preparation.operation

/** One timed call over a JCA engine: perCall decides what it redoes; the first instance is made and initialised here, before timing. */
internal class EngineCall<E : Any>(
    private val create: () -> E,
    private val init: (E, Int) -> Unit,
    private val operate: (E) -> Any?,
) {

    private var calls = 0

    var engine: E = create().also { init(it, calls++) }
        private set

    fun invocation(perCall: PerCall, exact: (Any?) -> Any? = { it }, readBack: Boolean = false): Invocation {
        val call: () -> Any? = when (perCall) {
            PerCall.OPERATION -> { { operate(engine) } }
            PerCall.INIT_AND_OPERATION -> { { init(engine, calls++); operate(engine) } }
            PerCall.INSTANCE_INIT_AND_OPERATION -> { { engine = create(); init(engine, calls++); operate(engine) } }
        }
        return Invocation(call, exact, if (readBack) { { engine } } else { { null } }, perCall)
    }
}
