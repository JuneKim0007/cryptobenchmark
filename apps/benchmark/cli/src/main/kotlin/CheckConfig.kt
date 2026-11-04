import io.github.junekim0007.cryptobench.config.AuthoredFiles
import io.github.junekim0007.cryptobench.config.global.ProvidersDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import java.io.File
import java.io.IOException
import kotlin.system.exitProcess

// The parse-only check before any build: the real parsers, no capture, nothing written; one YAML document on stdout.
fun main(arguments: Array<String>) {
    if (arguments.isEmpty()) {
        System.err.println("usage: checkconfig <global.yaml>...")
        exitProcess(2)
    }
    try {
        val checked = arguments.map { path ->
            val authored = AuthoredFiles().read(File(path))
            linkedMapOf("global" to path, "testSet" to authored.testSetFile.path,
                        "bundled" to ProvidersDocument.bundledList(authored.global.providers.bundled))
        }
        print(YamlCodec().dump(checked))
    } catch (expected: IllegalArgumentException) {
        fail(expected)
    } catch (expected: IllegalStateException) {
        fail(expected)
    } catch (expected: IOException) {
        fail(expected)
    }
}
