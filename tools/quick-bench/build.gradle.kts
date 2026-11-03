import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm") version "2.2.21"
    application
}

repositories { mavenCentral() }

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

sourceSets {
    main {
        kotlin.setSrcDirs(listOf(
            "../../modules/environment/discovery/src/main/kotlin",
            "../../modules/settings/src/main/kotlin",
            "../../modules/preparation/src/main/kotlin",
            "../../modules/benchmark/src/main/kotlin",
            "src/main/kotlin",
        ))
        resources.setSrcDirs(listOf("../../modules/preparation/src/main/resources"))
    }
}

dependencies { implementation("org.yaml:snakeyaml:2.3") }

application { mainClass.set(providers.gradleProperty("mainClass").orElse("BenchKt")) }
