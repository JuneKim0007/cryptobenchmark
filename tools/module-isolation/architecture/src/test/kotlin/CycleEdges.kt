package io.github.junekim0007.cryptobench.architecture

object CycleEdges {
    fun of(edges: Set<Pair<String, String>>): Set<Pair<String, String>> {
        val component = components(edges)
        return edges.filter { (a, b) -> component.getValue(a) == component.getValue(b) }.toSet()
    }

    private fun components(edges: Set<Pair<String, String>>): Map<String, Int> {
        val next = edges.groupBy({ it.first }, { it.second })
        val nodes = (edges.map { it.first } + edges.map { it.second }).toSortedSet()
        val index = HashMap<String, Int>()
        val low = HashMap<String, Int>()
        val stack = ArrayDeque<String>()
        val component = HashMap<String, Int>()
        fun visit(v: String) {
            index[v] = index.size; low[v] = index.getValue(v); stack.addLast(v)
            for (w in next[v].orEmpty()) {
                if (w !in index) { visit(w); low[v] = minOf(low.getValue(v), low.getValue(w)) }
                else if (w !in component) low[v] = minOf(low.getValue(v), index.getValue(w))
            }
            if (low[v] == index[v]) {
                do { val w = stack.removeLast(); component[w] = index.getValue(v) } while (w != v)
            }
        }
        nodes.forEach { if (it !in index) visit(it) }
        return component
    }
}
