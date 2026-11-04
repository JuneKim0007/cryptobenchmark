import java.security.MessageDigest;
import javax.crypto.Cipher;
import javax.crypto.Mac;
import javax.crypto.CipherOutputStream;

class Box {
    private final Mac mac = makeMac();
    private Cipher held;

    byte[] local(byte[] data, java.security.Key key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A"); // site: local
        c.init(Cipher.DECRYPT_MODE, key);
        return c.doFinal(data);
    }

    byte[] chain(byte[] data) throws Exception {
        return MessageDigest.getInstance("ALG-B").digest(data); // site: chain
    }

    private Mac makeMac() throws Exception {
        return Mac.getInstance("ALG-C"); // site: returned
    }

    byte[] tag(byte[] data) throws Exception {
        mac.init(new javax.crypto.spec.SecretKeySpec(new byte[] {1, 2}, "ALG-C"));
        return mac.doFinal(data);
    }

    void field(java.security.Key key) throws Exception {
        held = Cipher.getInstance("ALG-A"); // site: field
        held.init(Cipher.ENCRYPT_MODE, key);
    }

    byte[] seal(byte[] data) throws Exception {
        return held.doFinal(data);
    }

    void argument(java.io.OutputStream out, java.security.Key key) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A"); // site: wrapper
        c.init(Cipher.ENCRYPT_MODE, key);
        new CipherOutputStream(out, c).close();
    }

    void probe() {
        try {
            Cipher.getInstance("ALG-A"); // site: no_real_use
        } catch (Exception ignored) {
        }
    }

    void passed(byte[] data) throws Exception {
        consume(MessageDigest.getInstance("ALG-B"), data); // site: argument
    }

    private void consume(MessageDigest md, byte[] data) {
        md.digest(data);
    }
}
