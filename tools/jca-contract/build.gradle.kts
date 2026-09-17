// Runs :discovery's JCA contract test on any modern JDK. The main build is pinned to Gradle 6.5
// and Java 8 (see #11), so it cannot host a Java version matrix; this reuses the same sources.
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

sourceSets {
    main { kotlin.setSrcDirs(listOf("../../android/discovery/src/main/kotlin", "src/main/kotlin")) }
    test { kotlin.setSrcDirs(listOf("../../android/discovery/src/test/kotlin")) }
}

dependencies {
    implementation("org.json:json:20231013")
    testImplementation("junit:junit:4.13.2")
}

tasks.test {
    systemProperty("capture.out", layout.buildDirectory.file("capture/environment.json").get().asFile.path)
    testLogging { showStandardStreams = true }
}

application {
    mainClass.set("PlaygroundKt")
}
