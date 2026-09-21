package io.github.junekim0007.cryptobench.discovery.trial.call

import java.security.Key
import java.security.interfaces.DSAKey
import java.security.interfaces.ECKey
import java.security.interfaces.RSAKey
import javax.crypto.SecretKey
import javax.crypto.interfaces.DHKey

internal object KeyBits {

    /** Key size in bits where the key type states one; null for keys whose size is fixed by name. */
    fun of(key: Key): Int? = when (key) {
        is RSAKey -> key.modulus.bitLength()
        is ECKey -> key.params.curve.field.fieldSize
        is DSAKey -> key.params.p.bitLength()
        is DHKey -> key.params.p.bitLength()
        is SecretKey -> key.encoded?.size?.times(8)
        else -> null
    }
}
