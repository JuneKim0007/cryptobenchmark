import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    kotlin("jvm")
}

repositories { mavenCentral() }

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    testImplementation("com.tngtech.archunit:archunit:1.5.1")
    testImplementation("org.yaml:snakeyaml:2.3")
    testImplementation("junit:junit:4.13.2")
}

val checkedModules = listOf("jca", "discovery", "config", "preparation", "benchmark")
checkedModules.forEach { evaluationDependsOn(":$it") }

tasks.test {
    val classes = files(checkedModules.map { project(":$it").the<SourceSetContainer>()["main"].output.classesDirs })
    val layers = rootDir.resolve("layers.yaml")
    inputs.files(classes)
    inputs.file(layers)
    inputs.dir("frozen")
    workingDir = projectDir
    systemProperty("architecture.classes", classes.asPath)
    systemProperty("architecture.layers", layers.path)
    System.getProperties().stringPropertyNames().filter { it.startsWith("archunit.") }
        .forEach { systemProperty(it, System.getProperty(it)) }
    testLogging { showStandardStreams = true; exceptionFormat = org.gradle.api.tasks.testing.logging.TestExceptionFormat.FULL }
}
