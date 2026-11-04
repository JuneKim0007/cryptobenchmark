import io.github.junekim0007.cryptobench.discovery.adapter.DeviceRuntimeReader
import org.yaml.snakeyaml.Yaml

fun main() {
    val runtime = DeviceRuntimeReader.read()
    println(Yaml().dump(linkedMapOf(
        "sdkInt" to runtime.sdkInt,
        "osName" to runtime.osName,
        "osArch" to runtime.osArch,
        "javaVersion" to runtime.javaVersion,
        "javaVendor" to runtime.javaVendor,
        "javaRuntimeVersion" to runtime.javaRuntimeVersion,
    )))
}
