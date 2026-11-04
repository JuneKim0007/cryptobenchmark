package io.github.junekim0007.cryptobench.preparation.port

sealed class Availability {

    object Available : Availability()

    data class Unavailable(val reason: String) : Availability() {
        init {
            require(reason.isNotBlank()) { "missing_field: reason" }
        }
    }
}
