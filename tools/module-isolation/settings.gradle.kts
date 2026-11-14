rootProject.name = "module-isolation"

include("files", "jca", "document", "discovery", "config", "preparation", "benchmark", "architecture")

dependencyResolutionManagement {
    versionCatalogs { create("libs") { from(files("../../apps/benchmark/gradle/libs.versions.toml")) } }
}
