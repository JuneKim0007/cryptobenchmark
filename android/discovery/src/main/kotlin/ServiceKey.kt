package io.github.junekim0007.cryptobench.discovery

import java.util.Locale


// ServiceKey gives a pair o
internal data class ServiceKey(val type: String, val algorithm: String) {
    /**
     * Takes string variables:  JCA service 'type' and Cryptography 'Algorithm' 
     * and normalize strings to UPPER CASE with respect to different locale
     */

    override fun toString(): String = "$type.$algorithm"

    companion object {

        fun of(type: String, algorithm: String): ServiceKey = ServiceKey(fold(type), fold(algorithm))

        fun fold(value: String): String = value.uppercase(Locale.ROOT)
    }
}
