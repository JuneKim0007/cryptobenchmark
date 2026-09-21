package io.github.junekim0007.cryptobench.preparation.resolve

import io.github.junekim0007.cryptobench.preparation.parameter.bind.BindException
import io.github.junekim0007.cryptobench.preparation.parameter.bind.ParameterBinder
import io.github.junekim0007.cryptobench.preparation.request.Selection

/** Binds a selection's trees once, so a broken parameter rejects the selection instead of failing a run. */
internal class ParameterCheck(private val binder: ParameterBinder) {

    fun problem(selection: Selection): String? {
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
