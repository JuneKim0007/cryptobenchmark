package io.github.junekim0007.cryptobench.config

import io.github.junekim0007.cryptobench.config.contract.BenchmarkConfig
import io.github.junekim0007.cryptobench.config.generate.DefaultConfigBuilder
import io.github.junekim0007.cryptobench.config.source.CaptureSource
import io.github.junekim0007.cryptobench.config.source.TrialSource
import io.github.junekim0007.cryptobench.config.write.ConfigDocument
import io.github.junekim0007.cryptobench.config.write.ConfigFile
import io.github.junekim0007.cryptobench.config.write.YamlCodec
import java.io.File

/** The module's entry point: environment's two files in, default.yaml out; and default.yaml back in. */
class Configuration(
    private val output: ConfigFile,
    private val builder: DefaultConfigBuilder = DefaultConfigBuilder(),
    private val codec: YamlCodec = YamlCodec(),
) {

    fun generate(captureFile: File, trialFile: File): File {
        val capture = CaptureSource.read(captureFile.name, codec.load(captureFile.readText()))
        val trial = TrialSource.read(trialFile.name, codec.load(trialFile.readText()))
        return output.write(codec.dump(ConfigDocument.of(builder.build(capture, trial))))
    }

    fun read(configFile: File = output.file): BenchmarkConfig = ConfigDocument.parse(codec.load(configFile.readText()))
}
