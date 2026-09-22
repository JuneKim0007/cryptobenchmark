package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.parameter.bind.BindException
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.request.Selection

internal class SelectionCheck(private val binder: ParameterBinder) {

    fun problem(selection: Selection, operations: List<Operation>): String? {
        val unsupported = selection.operations - operations.toSet()
        if (unsupported.isNotEmpty()) {
            return "unsupported_operation: $unsupported for ${selection.type}, one of $operations"
        }
        if (selection.keyParameters.isNotEmpty() && selection.keySizes.isNotEmpty()) {
            return "key_parameters_and_key_sizes: set one; a key spec already fixes the size"
        }
        return try {
            if (selection.keyParameters.isNotEmpty()) binder.bind(selection.keyParameters, "key")
            if (selection.parameters.isNotEmpty()) binder.bind(selection.parameters, "parameters")
            null
        } catch (failure: BindException) {
            failure.message
        }
    }
}
