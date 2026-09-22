package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.operation.OperationDefinitions
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
        val definitions = operations.map { OperationDefinitions.of(it) }
        val unused = listOfNotNull(
            "keySizes".takeIf { selection.keySizes.isNotEmpty() && definitions.none { definition -> definition.consumesKeySize } },
            "key".takeIf { selection.keyParameters.isNotEmpty() && definitions.none { definition -> definition.consumesKeySpec } },
            "parameters".takeIf { selection.parameters.isNotEmpty() && definitions.none { definition -> definition.consumesParameters } },
        )
        if (unused.isNotEmpty()) {
            return "unused_setting: $unused reaches no call of $operations"
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
