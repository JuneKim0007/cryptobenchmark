package demo;

import java.security.MessageDigest;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.SecretKey;

class Held {
    private final Mac mac;

    Held(SecretKey key) throws Exception {
        mac = Mac.getInstance("ALG-M"); // site: j_held
        mac.init(key);
    }

    byte[] tag(byte[] data) throws Exception {
        return mac.doFinal(data);
    }
}

class Reinit {
    private final SecretKey key;
    private final Cipher held;

    Reinit(SecretKey key) throws Exception {
        this.key = key;
        held = Cipher.getInstance("ALG-A/X"); // site: j_reinit
    }

    byte[] again(byte[] data) throws Exception {
        held.init(Cipher.ENCRYPT_MODE, key);
        return held.doFinal(data);
    }
}

class Pair {
    private final Cipher sealer;
    private final Cipher opener;

    Pair(SecretKey key) throws Exception {
        sealer = Cipher.getInstance("ALG-A/X"); // site: j_seal
        sealer.init(Cipher.ENCRYPT_MODE, key);
        opener = Cipher.getInstance("ALG-A/X"); // site: j_open
        opener.init(Cipher.DECRYPT_MODE, key);
    }

    byte[] closed(byte[] data) throws Exception {
        return sealer.doFinal(data);
    }

    byte[] opened(byte[] data) throws Exception {
        return opener.doFinal(data);
    }
}

class PerCall {
    static byte[] once(byte[] data, SecretKey key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A/X"); // site: j_local
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(data);
    }

    static byte[] hash(byte[] data) throws Exception {
        return MessageDigest.getInstance("ALG-H").digest(data); // site: j_chain
    }
}

class Lazy {
    private final SecretKey key;
    private Cipher lazy;

    Lazy(SecretKey key) {
        this.key = key;
    }

    byte[] cached(byte[] data) throws Exception {
        if (lazy == null) {
            lazy = Cipher.getInstance("ALG-A/X"); // site: j_lazy
            lazy.init(Cipher.ENCRYPT_MODE, key);
        }
        return lazy.doFinal(data);
    }
}

class Escape {
    static Cipher make(SecretKey key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A/X"); // site: j_escape
        c.init(Cipher.ENCRYPT_MODE, key);
        return c;
    }
}

class Fresh {
    static byte[] fresh(byte[] data) throws Exception {
        KeyGenerator g = KeyGenerator.getInstance("ALG-A"); // site: j_generator
        SecretKey made = g.generateKey();
        Cipher c = Cipher.getInstance("ALG-A/X"); // site: j_consumer
        c.init(Cipher.ENCRYPT_MODE, made);
        return c.doFinal(data);
    }
}

class Twice {
    private final SecretKey key;

    Twice(SecretKey key) {
        this.key = key;
    }

    byte[] one(byte[] data) throws Exception {
        Cipher c = Cipher.getInstance("ALG-B/Y"); // site: j_same_a
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(data);
    }

    byte[] two(byte[] data) throws Exception {
        Cipher c = Cipher.getInstance("ALG-B/Y"); // site: j_same_b
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(data);
    }
}
