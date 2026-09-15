// Runs :discovery's JCA contract test on any modern JDK. The main build is pinned to Gradle 6.5
// and Java 8 (see #11), so it cannot host a Java version matrix; this reuses the same sources.
plugins {
    kotlin("jvm") version "2.0.21"
}

repositories { mavenCentral() }

// No toolchain on purpose: the point is to compile and run on whatever JDK the matrix picked.

sourceSets {
    main { kotlin.setSrcDirs(listOf("../../android/discovery/src/main/kotlin")) }
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
