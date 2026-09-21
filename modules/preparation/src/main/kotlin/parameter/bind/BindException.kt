package io.github.junekim0007.cryptobench.preparation.parameter.bind

class BindException(path: String, detail: String) : IllegalArgumentException("bind_failed: $path: $detail")
