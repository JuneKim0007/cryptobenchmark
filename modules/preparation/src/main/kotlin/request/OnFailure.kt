package io.github.junekim0007.cryptobench.preparation.request

/** effective.yaml's policy: STOP before anything runs, or SKIP what failed, record why, and continue. */
enum class OnFailure { STOP, SKIP }
