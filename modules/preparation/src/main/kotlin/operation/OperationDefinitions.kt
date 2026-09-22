package io.github.junekim0007.cryptobench.preparation.operation

import io.github.junekim0007.cryptobench.preparation.measurement.Operation

internal object OperationDefinitions {

    fun of(operation: Operation): OperationDefinition = when (operation) {
        Operation.ENCRYPT -> EncryptDefinition
        Operation.DECRYPT -> DecryptDefinition
        Operation.SIGN -> SignDefinition
        Operation.VERIFY -> VerifyDefinition
        Operation.DIGEST -> DigestDefinition
        Operation.COMPUTE_MAC -> ComputeMacDefinition
        Operation.GENERATE_KEY -> GenerateKeyDefinition
        Operation.GENERATE_KEY_PAIR -> GenerateKeyPairDefinition
        Operation.AGREE_KEY -> AgreeKeyDefinition
        Operation.TYPE_DEFAULT -> TypeDefaultDefinition
    }
}
