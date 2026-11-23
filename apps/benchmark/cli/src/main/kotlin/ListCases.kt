import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

// The ids BenchKt measures, one per line in listing order; nothing written. The runner orders them into each process's order file.
fun main(arguments: Array<String>) = command(arguments, "<capture> <trial> <${FileNames.EFFECTIVE}> <preparation directory>", { it.size == 4 }) {
    val effective = File(arguments[2])
    HostPlan(File(arguments[0]), File(arguments[1]), effective, File(arguments[3])).plan.list(effective, written = false).forEach { println(it.id) }
}
