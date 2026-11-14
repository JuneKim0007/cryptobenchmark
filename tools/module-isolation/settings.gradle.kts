rootProject.name = "module-isolation"

include("files", "jca", "discovery", "config", "preparation", "benchmark", "architecture")

dependencyResolutionManagement {
    versionCatalogs { create("libs") { from(files("../../apps/benchmark/gradle/libs.versions.toml")) } }
}
