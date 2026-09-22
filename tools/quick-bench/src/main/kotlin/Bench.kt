import io.github.junekim0007.cryptobench.discovery.write.CaptureDocument
import io.github.junekim0007.cryptobench.discovery.write.YamlCodec
import io.github.junekim0007.cryptobench.preparation.Preparation
import io.github.junekim0007.cryptobench.preparation.adapter.DiscoveryCapability
import io.github.junekim0007.cryptobench.preparation.input.CipherKeys
import io.github.junekim0007.cryptobench.preparation.input.OperationInput
import io.github.junekim0007.cryptobench.preparation.key.generate.KeyMaterial
import io.github.junekim0007.cryptobench.preparation.measurement.Operation
import io.github.junekim0007.cryptobench.preparation.prepare.PreparedCase
import io.github.junekim0007.cryptobench.preparation.report.SkipFile
import java.io.File
import java.security.Key
import java.security.KeyPairGenerator
import java.security.MessageDigest
import java.security.Signature
import java.security.spec.AlgorithmParameterSpec
import javax.crypto.Cipher
import javax.crypto.KeyAgreement
import javax.crypto.KeyGenerator
import javax.crypto.Mac

private var blackHole: Long = 0
private const val WARMUP_NANOS = 200_000_000L
private const val RUN_NANOS = 30_000_000L
private const val RUNS = 5

fun main(arguments: Array<String>) {
    val codec = YamlCodec()
    val capture = CaptureDocument.parse(codec.load(File(arguments[0]).readText()))
    val outputDirectory = File(arguments[3]).apply { mkdirs() }
    val run = Preparation(DiscoveryCapability(File(arguments[0]), File(arguments[1])), SkipFile(outputDirectory)).prepare(File(arguments[2]))
    System.err.println("prepared=${run.cases.size} skipped=${run.skipped.size}")

    val results = StringBuilder("{\n  \"runtime\": {\"javaVersion\": \"${capture.runtime.javaVersion}\", \"defaultKeySizeProperty\": \"${capture.runtime.defaultKeySizeProperty}\"},\n  \"cases\": [\n")
    run.cases.forEachIndexed { index, prepared ->
        val measurement = measure(prepared)
        results.append("    {\"id\": \"${prepared.case.id}\", \"type\": \"${prepared.case.type}\", \"algorithm\": \"${prepared.case.algorithm}\", \"provider\": \"${prepared.case.provider}\"")
        results.append(", \"operation\": \"${prepared.case.operation}\", \"keySize\": ${prepared.case.keySize}, \"inputSize\": ${prepared.case.inputSize}")
        results.append(", \"iterations\": ${measurement.iterations}, \"nanosPerOperation\": [${measurement.perOperation.joinToString(", ")}]}")
        results.append(if (index == run.cases.lastIndex) "\n" else ",\n")
        System.err.println("  ${prepared.case.id}: median ${measurement.perOperation.sorted()[RUNS / 2]} ns/op")
    }
    results.append("  ]\n}\n")
    File(outputDirectory, "benchmark.json").writeText(results.toString())
    System.err.println("blackHole=$blackHole")
    println(File(outputDirectory, "benchmark.json").path)
}

private class Measurement(val iterations: Int, val perOperation: List<Long>)

private fun measure(prepared: PreparedCase): Measurement {
    val operation = operationOf(prepared)
    var warmupIterations = 0L
    val warmupStart = System.nanoTime()
    while (System.nanoTime() - warmupStart < WARMUP_NANOS) {
        operation()
        warmupIterations++
    }
    val perIteration = (System.nanoTime() - warmupStart).toDouble() / warmupIterations
    val iterations = maxOf(1, (RUN_NANOS / maxOf(1.0, perIteration)).toInt())
    val perOperation = (1..RUNS).map {
        val start = System.nanoTime()
        repeat(iterations) { operation() }
        (System.nanoTime() - start) / iterations
    }
    return Measurement(iterations, perOperation)
}

private fun operationOf(prepared: PreparedCase): () -> Unit {
    val case = prepared.case
    val specs = specPool(prepared)
    var next = 0
    fun spec(): AlgorithmParameterSpec? = if (specs.isEmpty()) null else specs[next++ % specs.size]
    return when (case.operation) {
        Operation.DIGEST -> {
            val digest = MessageDigest.getInstance(case.algorithm, case.provider)
            val input = message(prepared)
            ({ blackHole += digest.digest(input).size })
        }
        Operation.COMPUTE_MAC -> {
            val macSpec = prepared.parameters?.next()
            val mac = Mac.getInstance(case.algorithm, case.provider)
                .apply { if (macSpec == null) init(secret(prepared.key)) else init(secret(prepared.key), macSpec) }
            val input = message(prepared)
            ({ blackHole += mac.doFinal(input).size })
        }
        Operation.ENCRYPT -> {
            val cipher = Cipher.getInstance(case.algorithm, case.provider)
            val key = CipherKeys.encrypting(prepared.key)
            val input = message(prepared)
            ({
                val parameters = spec()
                if (parameters == null) cipher.init(Cipher.ENCRYPT_MODE, key) else cipher.init(Cipher.ENCRYPT_MODE, key, parameters)
                blackHole += cipher.doFinal(input).size
            })
        }
        Operation.DECRYPT -> {
            val input = prepared.input as OperationInput.Ciphertext
            val cipher = Cipher.getInstance(case.algorithm, case.provider)
            val key = CipherKeys.decrypting(prepared.key)
            ({
                when {
                    input.spec != null -> cipher.init(Cipher.DECRYPT_MODE, key, input.spec)
                    input.providerParameters != null -> cipher.init(Cipher.DECRYPT_MODE, key, input.providerParameters)
                    else -> cipher.init(Cipher.DECRYPT_MODE, key)
                }
                blackHole += cipher.doFinal(input.bytes).size
            })
        }
        Operation.SIGN -> {
            val signature = Signature.getInstance(case.algorithm, case.provider).apply { initSign(pair(prepared.key).private) }
            val input = message(prepared)
            ({ signature.update(input); blackHole += signature.sign().size })
        }
        Operation.VERIFY -> {
            val input = prepared.input as OperationInput.SignedMessage
            val signature = Signature.getInstance(case.algorithm, case.provider).apply { initVerify(pair(prepared.key).public) }
            ({ signature.update(input.message); blackHole += if (signature.verify(input.signature)) 1 else 0 })
        }
        Operation.GENERATE_KEY -> {
            val generator = KeyGenerator.getInstance(case.algorithm, case.provider)
            val keySpec = prepared.keyParameters?.next()
            when {
                keySpec != null -> generator.init(keySpec)
                case.keySize != null -> generator.init(case.keySize)
            }
            ({ blackHole += generator.generateKey().encoded.size })
        }
        Operation.GENERATE_KEY_PAIR -> {
            val generator = KeyPairGenerator.getInstance(case.algorithm, case.provider)
            val pairSpec = prepared.keyParameters?.next()
            when {
                pairSpec != null -> generator.initialize(pairSpec)
                case.keySize != null -> generator.initialize(case.keySize)
            }
            ({ blackHole += generator.generateKeyPair().public.encoded.size })
        }
        Operation.AGREE_KEY -> {
            val pairs = (prepared.key as KeyMaterial.Pairs).pairs
            val agreement = KeyAgreement.getInstance(case.algorithm, case.provider)
            val agreementSpec = prepared.parameters?.next()
            ({
                if (agreementSpec == null) agreement.init(pairs.first().private) else agreement.init(pairs.first().private, agreementSpec)
                agreement.doPhase(pairs.last().public, true)
                blackHole += agreement.generateSecret().size
            })
        }
        Operation.TYPE_DEFAULT -> ({ blackHole += 0 })
    }
}

private fun specPool(prepared: PreparedCase): List<AlgorithmParameterSpec> {
    val parameters = prepared.parameters ?: return emptyList()
    return if (parameters.varies) (1..256).map { parameters.next() } else listOf(parameters.next())
}

private fun message(prepared: PreparedCase): ByteArray =
    (prepared.input as? OperationInput.Message)?.bytes ?: ByteArray(prepared.case.inputSize ?: 0)

private fun secret(key: KeyMaterial) = (key as KeyMaterial.Secret).key

private fun pair(key: KeyMaterial) = (key as KeyMaterial.Pairs).pairs.first()
