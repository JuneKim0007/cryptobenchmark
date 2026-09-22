import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21" apply false
}

val moduleDirectories = mapOf(
    "discovery" to "../../modules/environment/discovery",
    "config" to "../../modules/config",
    "preparation" to "../../modules/preparation",
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
        sourceSets["main"].kotlin.setSrcDirs(listOf(File(moduleDirectory, "src/main/kotlin")))
        sourceSets["test"].kotlin.setSrcDirs(listOf(File(moduleDirectory, "src/test/kotlin")))
    }

    dependencies {
        "implementation"("org.yaml:snakeyaml:2.3")
        "testImplementation"("junit:junit:4.13.2")
    }

    tasks.withType<Test>().configureEach {
        workingDir = moduleDirectory
        systemProperty("capture.dir", layout.buildDirectory.dir("capture").get().asFile.path)
        testLogging { showStandardStreams = true }
    }
}
