import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21"
}

repositories { mavenCentral() }

val androidJar: String = providers.gradleProperty("androidJar").orNull
    ?: System.getenv("ANDROID_HOME")?.let { home -> "$home/platforms/android-36/android.jar" }
    ?: error("set -PandroidJar=<path to platforms/android-N/android.jar> or ANDROID_HOME")

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_1_8)
        freeCompilerArgs.add("-no-jdk")
    }
}

java {
    sourceCompatibility = JavaVersion.VERSION_1_8
    targetCompatibility = JavaVersion.VERSION_1_8
}

sourceSets {
    main {
        kotlin.setSrcDirs(listOf(
            "../../modules/environment/discovery/src/main/kotlin",
            "../../modules/preparation/src/main/kotlin",
        ))
    }
}

dependencies {
    compileOnly(files(androidJar))
    implementation("org.yaml:snakeyaml:2.3")
}
