package io.github.junekim0007.cryptobench.preparation.device

import java.util.Locale

internal data class ServiceName(val type: String, val algorithm: String) {

    companion object {

        fun of(type: String, algorithm: String): ServiceName =
            ServiceName(fold(type), fold(algorithm))

        fun fold(value: String): String = value.uppercase(Locale.ROOT)
    }
}
