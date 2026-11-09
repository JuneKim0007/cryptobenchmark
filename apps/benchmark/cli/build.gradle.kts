// The host commands (probe, configure, bench, convert, merges, interop) and :discovery's JCA contract test on a JDK matrix.
// Standalone: configuring the root build needs the Android SDK.
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21"
    application
}

repositories { mavenCentral() }

// Compile at a fixed target, run on whatever JDK the matrix picked. Tying the target to the
// runner's JDK would make every new Java release fail here on the compiler rather than on the JCA,
// which is the opposite of what this check is for.
java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

apply(from = "../gradle/guide-resources.gradle")

sourceSets {
    main {
        kotlin.setSrcDirs(listOf(
            "../modules/jca/src/main/kotlin",
            "../modules/files/src/main/kotlin",
            "../modules/environment/discovery/src/main/kotlin",
            "../modules/settings/src/main/kotlin",
            "../modules/config/src/main/kotlin",
            "../modules/preparation/src/main/kotlin",
            "../modules/benchmark/src/main/kotlin",
            "src/main/kotlin",
        ))
        resources.setSrcDirs(listOf("../modules/preparation/src/main/resources"))
    }
    test {
        kotlin.setSrcDirs(listOf("../modules/jca/src/test/kotlin", "../modules/environment/discovery/src/test/kotlin", "../modules/config/src/test/kotlin", "src/test/kotlin"))
        resources.setSrcDirs(listOf("../modules/config/src/test/resources"))
    }
}

// -PbundledArtifacts=group:name:version,... : the providers.bundled of global.yaml on this JVM's classpath, as modules/android/build.gradle does.
val bundledArtifacts = providers.gradleProperty("bundledArtifacts").orElse("").get().split(',').map { it.trim() }.filter { it.isNotEmpty() }

dependencies {
    bundledArtifacts.forEach { implementation(it) }
    implementation("org.yaml:snakeyaml:2.3")
    testImplementation("junit:junit:4.13.2")
}

// The example tests read each module's example/ directory relative to the module, so they belong to
// tools/module-isolation, which runs each module from its own directory.
tasks.test {
    filter { excludeTestsMatching("*ExampleFilesTest") }
    systemProperty("capture.dir", layout.buildDirectory.dir("capture").get().asFile.path)
    testLogging { showStandardStreams = true }
}

application {
    mainClass.set(providers.gradleProperty("mainClass").orElse("ProbeKt"))
}
