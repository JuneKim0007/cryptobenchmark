package io.github.junekim0007.cryptobench.preparation.peer

/** What a consumer cannot take, with its code; [Outcomes] decides the verdict. */
class PeerRefusal(val code: String, detail: String) : Exception(detail)
