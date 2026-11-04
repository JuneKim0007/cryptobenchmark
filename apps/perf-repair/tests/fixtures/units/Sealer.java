package demo;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.Signature;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;
import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.SecretKeySpec;

class Held {
    private Cipher seal;
    private Cipher open;

    Held(char[] words) throws Exception {
        SecretKeyFactory factory = SecretKeyFactory.getInstance("KDF-A"); // site: factory
        SecretKey made = factory.generateSecret(new Spec(words));
        seal = Cipher.getInstance("ALG-A/X"); // site: seal
        seal.init(Cipher.ENCRYPT_MODE, made);
        open = Cipher.getInstance("ALG-A/X"); // site: open
        open.init(Cipher.DECRYPT_MODE, made);
    }

    byte[] closed(byte[] data) throws Exception {
        return seal.doFinal(data);
    }

    byte[] opened(byte[] data) throws Exception {
        return open.doFinal(data);
    }
}

class Fed {
    static SecretKey make() throws Exception {
        KeyGenerator g = KeyGenerator.getInstance("ALG-B"); // site: generator
        return g.generateKey();
    }

    static byte[] enc(byte[] data, SecretKey key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-B/Y"); // site: fed_enc
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(data);
    }

    static byte[] dec(byte[] data, SecretKey key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-B/Y"); // site: fed_dec
        c.init(Cipher.DECRYPT_MODE, key);
        return c.doFinal(data);
    }

    static byte[] rawEnc(byte[] data, byte[] raw) throws Exception {
        Cipher c = Cipher.getInstance("ALG-C/Z"); // site: raw_enc
        c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(raw, "ALG-C"));
        return c.doFinal(data);
    }

    static byte[] rawDec(byte[] data, byte[] raw) throws Exception {
        Cipher c = Cipher.getInstance("ALG-C/Z"); // site: raw_dec
        c.init(Cipher.DECRYPT_MODE, new SecretKeySpec(raw, "ALG-C"));
        return c.doFinal(data);
    }
}

class Independent {
    private static final byte[] FIRST = {1};
    private static final byte[] SECOND = {2};

    void both(byte[] a, byte[] b) throws Exception {
        Mac first = Mac.getInstance("MAC-A"); // site: mac_first
        first.init(new SecretKeySpec(FIRST, "MAC-A"));
        first.doFinal(a);
        Mac second = Mac.getInstance("MAC-A"); // site: mac_second
        second.init(new SecretKeySpec(SECOND, "MAC-A"));
        second.doFinal(b);
    }
}

class OneLine {
    static PublicKey publicOne() throws Exception {
        KeyPairGenerator g = KeyPairGenerator.getInstance("PAIR-A"); // site: pair
        return g.generateKeyPair().getPublic();
    }

    byte[] sign(PrivateKey signing, PublicKey other, byte[] data) throws Exception {
        Signature s = Signature.getInstance("SIG-A"); // site: signer
        s.initSign(signing);
        s.update(data);
        return s.sign();
    }

    void twoKeys(byte[] left, byte[] right, byte[] data) throws Exception {
        Mac a = Mac.getInstance("MAC-B"); // site: left
        a.init(new SecretKeySpec(left, "MAC-B"));
        a.doFinal(data);
        Mac b = Mac.getInstance("MAC-B"); // site: right
        b.init(new SecretKeySpec(right, "MAC-B"));
        b.doFinal(data);
    }

    void unused() throws Exception {
        Mac never = Mac.getInstance("MAC-B"); // site: never
    }
}
