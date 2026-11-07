package io.github.junekim0007.cryptobench.benchmark

import io.github.junekim0007.cryptobench.benchmark.run.HostHarness
import io.github.junekim0007.cryptobench.benchmark.run.OutputHook
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.operation.Invocations
import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File
import java.security.MessageDigest

class CheckModeTest {

    private val timedSources = listOf(
        File("src/main/kotlin/run/TimedLoop.kt"), File("src/main/kotlin/run/compose"), File("src/main/kotlin/run/decorate"),
        File("../android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/CryptoBenchmark.kt"),
        File("../android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/PinnedCase.kt"),
    )

    @Test
    fun theHookIsAbsentFromEveryTimedPath() {
        val mentioning = timedSources.flatMap { it.walkTopDown().filter(File::isFile).toList() }.filter { "OutputHook" in it.readText() || "hook" in it.readText() }
        assertEquals(emptyList<File>(), mentioning)
        assertEquals("the timed loops feed the BlackHole only", emptyList<String>(), timedBodies().filter { "hook" in it })
    }

    @Test
    fun onceHandsExactlyOneExactOutputToTheHook() {
        val prepared = CheckFixture.digest()
        val hook = OutputHook()
        HostHarness.ONCE.call(Invocations.of(prepared), hook)
        assertEquals(1, hook.outputs.size)
        val message = (prepared.input as OperationInput.Message).bytes
        assertArrayEquals(MessageDigest.getInstance("SHA-256").digest(message), hook.outputs.single() as ByteArray)
    }

    // The bodies of the two timed loops: HostHarness.measure and JetpackCase.timed.
    private fun timedBodies(): List<String> = listOf(
        body(File("src/main/kotlin/run/HostHarness.kt"), "fun measure("),
        body(File("../android/src/androidTest/kotlin/io/github/junekim0007/cryptobench/JetpackCase.kt"), "fun timed("),
    )

    private fun body(file: File, start: String): String {
        val text = file.readText()
        val from = text.indexOf(start).also { check(it >= 0) { "$start not in $file" } }
        var depth = 0
        for (index in text.indexOf('{', from) until text.length) {
            when (text[index]) {
                '{' -> depth++
                '}' -> if (--depth == 0) return text.substring(from, index + 1)
            }
        }
        error("unbalanced: $file")
    }
}
