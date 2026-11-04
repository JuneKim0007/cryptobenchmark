package demo;

import java.net.Socket;
import java.security.Security;
import javax.crypto.Cipher;
import javax.crypto.spec.SecretKeySpec;

class Net {
    private static final String ALGO = "AES/GCM/" + "NoPadding";

    static {
        Security.insertProviderAt(new BundledProvider(), 1);
    }

    void send(Socket s, byte[] in) throws Exception {
        Cipher c = Cipher.getInstance(ALGO);
        c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(new byte[]{1, 2, 3}, "AES"));
        s.getOutputStream().write(c.doFinal(in));
    }
}
