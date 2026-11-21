import io.github.junekim0007.cryptobench.discovery.adapter.DeviceRuntimeReader
import io.github.junekim0007.cryptobench.document.YamlCodec

fun main(arguments: Array<String>) = command(arguments, "runtimefields (no arguments)", { it.all(String::isBlank) }) {
    val runtime = DeviceRuntimeReader.read()
    println(YamlCodec.DOCUMENT.dump(linkedMapOf(
        "sdkInt" to runtime.sdkInt,
        "osName" to runtime.osName,
        "osArch" to runtime.osArch,
        "javaVersion" to runtime.javaVersion,
        "javaVendor" to runtime.javaVendor,
        "javaRuntimeVersion" to runtime.javaRuntimeVersion,
    )))
}
