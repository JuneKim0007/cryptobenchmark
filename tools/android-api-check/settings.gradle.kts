rootProject.name = "android-api-check"

dependencyResolutionManagement {
    versionCatalogs { create("libs") { from(files("../../apps/benchmark/gradle/libs.versions.toml")) } }
}
