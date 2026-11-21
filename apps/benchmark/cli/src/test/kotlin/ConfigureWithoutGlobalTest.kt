import io.github.junekim0007.cryptobench.discovery.Discovery
import io.github.junekim0007.cryptobench.discovery.write.ProbeDirectory
import io.github.junekim0007.cryptobench.files.FileNames
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File
import java.security.Security
import java.util.concurrent.TimeUnit

/** ConfigureKt given no global.yaml looks for none: it writes the inventory alone and warns, in its own JVM. */
class ConfigureWithoutGlobalTest {

    @get:Rule
    val folder = TemporaryFolder()

    @Test
    fun noGlobalArgumentWritesOnlyTheInventory() {
        val discovery = Discovery(ProbeDirectory(folder.newFolder("discovery")))
        val probe = discovery.probe(Security.getProviders())
        val trialFile = discovery.trial(probe.capture, Security.getProviders()).trialFile
        val out = File(folder.root, "configuration")
        val java = File(System.getProperty("java.home"), "bin/java").path
        val process = ProcessBuilder(java, "-cp", System.getProperty("java.class.path"), "ConfigureKt", probe.captureFile.path, trialFile.path, out.path)
            .directory(folder.root).start()
        process.outputStream.close()
        val stderr = process.errorStream.bufferedReader().readLines()
        process.inputStream.readBytes()
        assertTrue("ConfigureKt did not end", process.waitFor(120, TimeUnit.SECONDS))
        assertEquals(0, process.exitValue())
        assertTrue(stderr.joinToString("\n"), "warning: no ${FileNames.GLOBAL} given; ${FileNames.EFFECTIVE} not written" in stderr)
        assertEquals(listOf(FileNames.INVENTORY), out.list()!!.sorted())
    }
}
