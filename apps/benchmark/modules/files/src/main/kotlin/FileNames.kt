package io.github.junekim0007.cryptobench.files

/** Every file a stage reads or writes by name; python's CONTRACT must agree (tools/module-isolation/names_check.py). */
object FileNames {
    const val GLOBAL = "global.yaml"
    const val INVENTORY = "inventory.yaml"
    const val EFFECTIVE = "effective.yaml"
    const val CONFIG_REPORT = "report.yaml"
    const val GUIDE = "guide.yaml"
    const val KNOWN_ANSWERS = "known-answers.yaml"
    const val PREPARED = "prepared.yaml"
    const val SKIPPED = "skipped.yaml"
    const val CHECK_RESULT = "check.yaml"
    const val BENCHMARK_JSON = "benchmark.json"
    const val ENERGY_CAPABILITY = "energy.yaml"
    const val ENERGY_JSON = "energy.json"
    const val ENERGY_DRY = "energy-dry.yaml"
    const val INTEROP_PLAN = "interop_plan.yaml"
    const val INTEROP_RESULT = "interop.yaml"
    const val SCOPED_INTEROP = "scoped-interop.yaml"
    const val CPU_PINS = "cpu-pins.yaml"
    const val ALGORITHM_NAMES = "algorithm-names.yaml"
    const val ENGINE_OPERATIONS = "engine-operations.yaml"
    const val SETUP_CATALOG = "setup-catalog.yaml"
}
