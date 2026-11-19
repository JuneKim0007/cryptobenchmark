package io.github.junekim0007.cryptobench.benchmark.check

// A host process measures its cases in the order the runner wrote, which must name each listed case once.
object LaunchOrder {

    fun of(listed: List<String>, text: String): List<String> {
        val order = text.split(Regex("\\s+")).filter { it.isNotEmpty() }
        check(order.sorted() == listed.sorted()) {
            "order_mismatch: ${order.size} ids for ${listed.size} listed cases; not listed ${order.filterNot { it in listed }.distinct()}, " +
                "missing ${listed.filterNot { it in order }}"
        }
        return order
    }
}
