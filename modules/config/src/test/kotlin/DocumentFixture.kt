package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.effective.EffectiveBuilder
import io.github.junekim0007.cryptobench.config.global.GlobalDocument
import io.github.junekim0007.cryptobench.config.inventory.InventoryBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.testset.TestSetDocument
import io.github.junekim0007.cryptobench.config.yaml.YamlCodec
import io.github.junekim0007.cryptobench.config.yaml.YamlFiles
import java.io.File
import java.nio.file.Files

/** The same built documents every document test starts from, so no test class repeats the setup. */
internal class DocumentFixture {
    val files = YamlFiles()
    val codec = YamlCodec()
    val directory: File = Files.createTempDirectory("documents").toFile()
    val inventory = InventoryBuilder().build(
        CaptureSource.parse(codec.load(Fixtures.CAPTURE)), TrialSource.parse(codec.load(Fixtures.TRIAL)), InventoryBuilder.Files("probe_x.yaml", "trial_x.yaml"))
    val global = GlobalDocument.parse(codec.load(Fixtures.GLOBAL))
    val testSet = TestSetDocument.parse(codec.load(Fixtures.TEST_SET))
    val effective = EffectiveBuilder().build(global, testSet, inventory, EffectiveBuilder.Files("global.yaml", "testsets/scope.yaml", "inventory.yaml"))
}
