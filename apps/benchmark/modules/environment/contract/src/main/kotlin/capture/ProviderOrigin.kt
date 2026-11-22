package io.github.junekim0007.cryptobench.contract.capture

import java.util.Locale

enum class ProviderOrigin {
    PLATFORM,
    BUNDLED;

    val key: String get() = name.lowercase(Locale.ROOT)

    companion object {

        fun of(key: String): ProviderOrigin =
            entries.firstOrNull { it.key == key } ?: throw IllegalArgumentException("invalid: origin $key, one of ${entries.map { it.key }}")
    }
}
