package io.github.junekim0007.cryptobench.jca.bind

class BindException(path: String, detail: String) : IllegalArgumentException("bind_failed: $path: $detail")
