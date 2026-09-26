import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21" apply false
}

val moduleDirectories = mapOf(
    "discovery" to "../../modules/environment/discovery",
    "config" to "../../modules/config",
    "preparation" to "../../modules/preparation",
    "benchmark" to "../../modules/benchmark",
)

subprojects {
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
            rootDir.resolve(moduleDirectories.getValue("preparation")).resolve("src/main/kotlin").takeIf { name == "benchmark" },
        )
        sourceSets["main"].kotlin.setSrcDirs(sources)
        sourceSets["test"].kotlin.setSrcDirs(listOf(File(moduleDirectory, "src/test/kotlin")))
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
