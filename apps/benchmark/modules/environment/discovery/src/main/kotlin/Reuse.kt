package io.github.junekim0007.cryptobench.discovery

import io.github.junekim0007.cryptobench.document.versioned.FileRefusal
import java.io.File

sealed interface Reuse

data class Reprobe(val reason: String) : Reuse {

    companion object {
        // a versioned read refuses with <code>: <file>: <rest>; anything else (an unreadable file's IOException) is uncoded and gets the file here
        fun refused(file: File, failure: Throwable): Reprobe = Reprobe(
            if (failure is IllegalArgumentException) failure.message.orEmpty().lineSequence().first()
            else FileRefusal.of(file.name, "${failure.javaClass.simpleName}: ${failure.message}"),
        )
    }
}
