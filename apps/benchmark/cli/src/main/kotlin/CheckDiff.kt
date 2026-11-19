import io.github.junekim0007.cryptobench.benchmark.verify.record.CheckFile
import io.github.junekim0007.cryptobench.benchmark.verify.record.RecordDiff
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File
import kotlin.system.exitProcess

// Two check.yaml files, baseline first: every difference on stdout; exit 3 when there is any (1 is an error), so a change shows its diff or none.
fun main(arguments: Array<String>) = command(arguments, "<baseline ${FileNames.CHECK_RESULT}> <current ${FileNames.CHECK_RESULT}>", { it.size == 2 }) {
    val differences = RecordDiff.of(CheckFile.cases(File(arguments[0])), CheckFile.cases(File(arguments[1])))
    differences.forEach(::println)
    System.err.println("differences=${differences.size}")
    if (differences.isNotEmpty()) exitProcess(DIFFERENT)
}

// exit 1 is an error, as for every main
private const val DIFFERENT = 3
