package io.github.junekim0007.cryptobench.benchmark.run

import io.github.junekim0007.cryptobench.preparation.operation.Invocation

// One untimed call through a harness, its output handed to the hook: HostHarness.ONCE on the host, a Jetpack dry run on a device.
fun interface OneCall {
    fun call(invocation: Invocation, hook: OutputHook)
}
