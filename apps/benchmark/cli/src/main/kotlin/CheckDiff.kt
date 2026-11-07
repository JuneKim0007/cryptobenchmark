import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.RecordDiff
import java.io.File
import kotlin.system.exitProcess

// Two check.yaml files, baseline first: every difference on stdout; exit 1 when there is any, so a change shows its diff or none.
fun main(arguments: Array<String>) {
    if (arguments.size != 2) {
        System.err.println("usage: <baseline check.yaml> <current check.yaml>")
        exitProcess(2)
    }
    val differences = RecordDiff.of(CheckFile.cases(File(arguments[0])), CheckFile.cases(File(arguments[1])))
    differences.forEach(::println)
    System.err.println("differences=${differences.size}")
    exitProcess(if (differences.isEmpty()) 0 else 1)
}
