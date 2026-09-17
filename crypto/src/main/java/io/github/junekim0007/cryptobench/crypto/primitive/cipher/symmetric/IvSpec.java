package io.github.junekim0007.cryptobench.crypto.primitive.cipher.symmetric;

import java.security.spec.AlgorithmParameterSpec;
import java.util.Locale;

import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.IvParameterSpec;

/**
 * The parameter spec a symmetric cipher needs for its mode. One place, so encrypt and decrypt
 * cannot disagree about IV length or spec type.
 */
final class IvSpec {

    static final int GCM_TAG_BITS = 128;
    static final int GCM_IV_BYTES = 12;
    static final int DES_IV_BYTES = 8;
    static final int AES_IV_BYTES = 16;

    private IvSpec() {
    }

    /** ECB and "no mode" take no IV; a bare algorithm name resolves to ECB. */
    static boolean usesIv(String mode) {
        return mode != null && !mode.isEmpty() && !"ECB".equals(mode.toUpperCase(Locale.ROOT));
    }

    static boolean isGcm(String mode) {
        String normalised = mode == null ? "" : mode.toUpperCase(Locale.ROOT);
        return normalised.equals("GCM") || normalised.equals("GCM-SIV");
    }

    /** IV length in bytes: 12 for GCM, the cipher block size otherwise. */
    static int initializationVectorBytes(String algorithm, String mode) {
        if (isGcm(mode)) {
            return GCM_IV_BYTES;
        }
        String normalised = algorithm == null ? "" : algorithm.toUpperCase(Locale.ROOT);
        return normalised.startsWith("DES") || normalised.equals("3DES") ? DES_IV_BYTES : AES_IV_BYTES;
    }

    /** Spec to initialise an encrypting cipher with, or null when the mode takes no IV. */
    static AlgorithmParameterSpec forEncrypt(String algorithm, String mode) {
        if (!usesIv(mode)) {
            return null;
        }
        byte[] initializationVector = new byte[initializationVectorBytes(algorithm, mode)];
        return isGcm(mode)
                ? new GCMParameterSpec(GCM_TAG_BITS, initializationVector)
                : new IvParameterSpec(initializationVector);
    }

    /** Spec rebuilt from the IV the encrypting cipher reported, or null when the mode takes no IV. */
    static AlgorithmParameterSpec forDecrypt(String mode, byte[] initializationVector) {
        if (!usesIv(mode) || initializationVector == null) {
            return null;
        }
        return isGcm(mode)
                ? new GCMParameterSpec(GCM_TAG_BITS, initializationVector)
                : new IvParameterSpec(initializationVector);
    }
}
