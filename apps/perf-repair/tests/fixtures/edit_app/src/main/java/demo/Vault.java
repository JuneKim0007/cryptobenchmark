package demo;

import java.security.Security;
import javax.crypto.Cipher;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

class Vault {
    static final String ALG = "AES/GCM/NoPadding";
    private final SecretKey key;

    Vault(SecretKey key) {
        this.key = key;
    }

    byte[] literal(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding", "Slow");
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(in);
    }

    byte[] absent(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, this.key);
        return c.doFinal(in);
    }

    byte[] lookedUp(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance(ALG, Security.getProvider("Slow"));
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(in);
    }

    byte[] multiLine(byte[] in, byte[] iv) throws Exception {
        Cipher c = Cipher.getInstance(
            "AES/GCM/NoPadding", // the app's choice
            "Slow");
        c.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(96, iv));
        return c.doFinal(in);
    }

    byte[] nested(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance(name(prefix("AES"), "GCM"), "Slow");
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(in);
    }

    byte[] twice(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, key);
        c.init(Cipher.ENCRYPT_MODE, key);
        return c.doFinal(in);
    }

    String prefix(String a) {
        return a;
    }

    String name(String a, String b) {
        return a + "/" + b + "/NoPadding";
    }
}
