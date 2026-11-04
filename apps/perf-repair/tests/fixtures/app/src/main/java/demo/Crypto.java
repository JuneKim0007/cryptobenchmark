package demo;

import java.security.MessageDigest;
import java.security.Security;
import javax.crypto.Cipher;
import javax.crypto.Mac;

class Crypto {
    static final String ALG = "AES/GCM/NoPadding";

    byte[] seal(byte[] in) throws Exception {
        Cipher c = Cipher.getInstance("aes/gcm/nopadding", "Slow");
        return c.doFinal(in);
    }

    byte[] hash(byte[] in) throws Exception {
        return MessageDigest.getInstance("SHA256").digest(in);
    }

    Cipher byConstant() throws Exception {
        return Cipher.getInstance(ALG, Security.getProvider("Fast"));
    }

    Mac mac() throws Exception {
        return Mac.getInstance(
            "HmacSHA256",
            new BundledProvider());
    }

    Cipher bundled() throws Exception {
        return Cipher.getInstance("AES/GCM/NoPadding", "Bundled");
    }
}
