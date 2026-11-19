package io.github.junekim0007.cryptobench.preparation.peer

import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.IvParameterSpec

/** Which of the call's parameters reach the consumer: every one it used, or only what a message carries (an IV, GCM's nonce and tag length). */
enum class Travel {
    USED,
    MESSAGE_BORNE;

    fun carried(used: Any?): Any? = if (this == USED) used else used.takeIf { it is IvParameterSpec || it is GCMParameterSpec }
}
