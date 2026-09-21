package io.github.junekim0007.cryptobench.preparation.parameter.bind

/** Names the path in the tree that failed, so a hand-edited file points at its own mistake. */
class BindException(path: String, detail: String) : IllegalArgumentException("bind_failed: $path: $detail")
