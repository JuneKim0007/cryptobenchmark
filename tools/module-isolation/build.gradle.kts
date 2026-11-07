import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21" apply false
}

val moduleDirectories = mapOf(
    "discovery" to "../../apps/benchmark/modules/environment/discovery",
    "config" to "../../apps/benchmark/modules/config",
    "preparation" to "../../apps/benchmark/modules/preparation",
    "benchmark" to "../../apps/benchmark/modules/benchmark",
)

configure(subprojects.filter { it.name in moduleDirectories }) {
    apply(plugin = "org.jetbrains.kotlin.jvm")

    repositories { mavenCentral() }

    extensions.configure<JavaPluginExtension> {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    val moduleDirectory = rootDir.resolve(moduleDirectories.getValue(name))

    extensions.configure<org.jetbrains.kotlin.gradle.dsl.KotlinJvmProjectExtension> {
        compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
        val sources = listOfNotNull(
            File(moduleDirectory, "src/main/kotlin"),
            rootDir.resolve("../../apps/benchmark/modules/settings/src/main/kotlin").takeIf { name != "discovery" },
            rootDir.resolve(moduleDirectories.getValue("preparation")).resolve("src/main/kotlin").takeIf { name == "benchmark" },
        )
        sourceSets["main"].kotlin.setSrcDirs(sources)
        sourceSets["test"].kotlin.setSrcDirs(listOf(File(moduleDirectory, "src/test/kotlin")))
    }

    val resourceDirectories = listOfNotNull(File(moduleDirectory, "src/main/resources"),
        rootDir.resolve(moduleDirectories.getValue("preparation")).resolve("src/main/resources").takeIf { name == "benchmark" })
    extensions.configure<SourceSetContainer> {
        named("main") { resources.setSrcDirs(resourceDirectories) }
        named("test") { resources.setSrcDirs(listOf(File(moduleDirectory, "src/test/resources"))) }
    }

    dependencies {
        "implementation"("org.yaml:snakeyaml:2.3")
        "testImplementation"("junit:junit:4.13.2")
    }

    tasks.withType<Test>().configureEach {
        workingDir = moduleDirectory
        systemProperty("capture.dir", layout.buildDirectory.dir("capture").get().asFile.path)
        System.getProperty("examples.update")?.let { systemProperty("examples.update", it) }
        testLogging { showStandardStreams = true }
    }
}
