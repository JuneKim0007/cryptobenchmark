package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase

object Invocations {

    fun of(prepared: PreparedCase): Invocation = OperationDefinitions.of(prepared.case.operation).invocation(prepared)
}
