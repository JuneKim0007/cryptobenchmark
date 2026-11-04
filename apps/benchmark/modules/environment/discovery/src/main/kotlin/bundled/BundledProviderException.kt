package io.github.junekim0007.cryptobench.discovery.bundled

class BundledProviderException(val code: String, detail: String, cause: Throwable? = null) : IllegalArgumentException("$code: $detail", cause)
