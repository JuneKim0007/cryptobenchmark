package io.github.junekim0007.cryptobench.preparation.port

sealed class Availability {

    object Available : Availability()

    // registered: the provider has the service, only its default-run trial failed
    data class Unavailable(val reason: String, val registered: Boolean = false) : Availability() {
        init {
            require(reason.isNotBlank()) { "missing_field: reason" }
        }
    }
}
