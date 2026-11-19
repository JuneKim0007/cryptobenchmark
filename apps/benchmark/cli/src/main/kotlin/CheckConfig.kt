import io.github.junekim0007.cryptobench.config.AuthoredFiles
import io.github.junekim0007.cryptobench.config.global.ProvidersDocument
import io.github.junekim0007.cryptobench.document.YamlCodec
import io.github.junekim0007.cryptobench.files.FileNames
import java.io.File

// The parse-only check before any build: the real parsers, no capture, nothing written; one YAML document on stdout.
fun main(arguments: Array<String>) = command(arguments, "checkconfig <${FileNames.GLOBAL}>...", { it.isNotEmpty() }) {
    val checked = arguments.map { path ->
        val authored = AuthoredFiles().read(File(path))
        linkedMapOf("global" to path, "testSet" to authored.testSetFile.path,
                    "bundled" to ProvidersDocument.bundledList(authored.global.providers.bundled))
    }
    print(YamlCodec.DOCUMENT.dump(checked))
}
