package io.github.junekim0007.cryptobench.benchmark.run.decorate

import io.github.junekim0007.cryptobench.benchmark.run.compose.CaseRun

class Cooldown(private val inner: CaseRun, private val millis: Long, private val sleep: (Long) -> Unit = Thread::sleep) : CaseRun {

    override fun run(): Long? {
        val calls = inner.run()
        if (millis > 0) sleep(millis)
        return calls
    }
}
