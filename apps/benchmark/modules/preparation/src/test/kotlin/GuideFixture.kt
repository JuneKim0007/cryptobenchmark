import io.github.junekim0007.cryptobench.preparation.shared.YamlCodec
import java.io.File

/** A guide.yaml with one bare item for every item of the effective file beside it: the tests that are not about the guide. */
object GuideFixture {

    @Suppress("UNCHECKED_CAST")
    fun beside(effective: File): File {
        val document = YamlCodec().load(effective.readText()) as Map<String, Any>
        val providers = document["providers"] as Map<String, Map<String, Map<String, Any>>>
        val items = providers.mapValues { (_, types) -> types.mapValues { (_, names) -> names.keys.associate { it.substringBefore('@') to emptyMap<String, Any>() } } }
        File(effective.absoluteFile.parentFile, "guide.yaml").writeText(YamlCodec().dump(mapOf("schemaVersion" to 1, "items" to items)))
        return effective
    }
}
