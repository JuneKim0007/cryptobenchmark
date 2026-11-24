package io.github.junekim0007.cryptobench.preparation.device

import io.github.junekim0007.cryptobench.document.names.AlgorithmNames

internal data class ServiceName(val type: String, val algorithm: String) {

    companion object {

        fun of(type: String, algorithm: String): ServiceName =
            ServiceName(AlgorithmNames.fold(type), AlgorithmNames.fold(algorithm))
    }
}
