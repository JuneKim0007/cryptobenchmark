import java.security.Key;
import java.security.KeyStore;
import javax.crypto.Cipher;
import javax.crypto.Mac;

class Vault {
    private Key held;
    private Key many;
    private final KeyStore store = null;
    private final Prefs prefs = null;

    Vault(Key given) {
        held = given;
    }

    void rotate() throws Exception {
        held = prefs.fetch("a");
    }

    byte[] byField(byte[] data) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A"); // site: field_key
        c.init(Cipher.ENCRYPT_MODE, held);
        return c.doFinal(new byte[] {1});
    }

    private Key loaded() throws Exception {
        return store.getKey("a", null);
    }

    byte[] byCall() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: call_key
        m.init(loaded());
        return m.doFinal(new byte[] {1});
    }

    private Key opaque() throws Exception {
        return prefs.fetch("b");
    }

    byte[] byOpaqueCall() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: opaque_key
        m.init(opaque());
        return m.doFinal(new byte[] {1});
    }

    public byte[] open(Key key) throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: public_key
        m.init(key);
        return m.doFinal(new byte[] {1});
    }

    byte[] callsOpen() throws Exception {
        return open(store.getKey("c", null));
    }

    public byte[] nobody(Key key) throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: no_caller
        m.init(key);
        return m.doFinal(new byte[] {1});
    }

    byte[] closed() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: closed
        m.init(store.getKey("d", null));
        return m.doFinal(new byte[] {1});
    }

    void w1() { many = prefs.fetch("1"); }
    void w2() { many = prefs.fetch("2"); }
    void w3() { many = prefs.fetch("3"); }
    void w4() { many = prefs.fetch("4"); }
    void w5() { many = prefs.fetch("5"); }
    void w6() { many = prefs.fetch("6"); }
    void w7() { many = prefs.fetch("7"); }
    void w8() { many = prefs.fetch("8"); }
    void w9() { many = prefs.fetch("9"); }

    byte[] overBudget() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: over_budget
        m.init(many);
        return m.doFinal(new byte[] {1});
    }

    private static final int SIZE = 16;

    byte[] sized(Key k) throws Exception {
        Cipher c = Cipher.getInstance("ALG-A"); // site: array_size
        byte[] iv = new byte[SIZE];
        c.init(Cipher.ENCRYPT_MODE, k, new javax.crypto.spec.IvParameterSpec(iv));
        return c.doFinal(new byte[] {1});
    }

    byte[] join(String a) throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: join
        m.init(store.getKey("f", null));
        return m.doFinal(("c-" + a).getBytes());
    }

    byte[] branch(boolean flag) throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: branch
        m.init(flag ? held : opaque());
        return m.doFinal(new byte[] {1});
    }

    byte[] closedPaths() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: closed_paths
        m.init(chosen());
        return m.doFinal(new byte[] {1});
    }

    private Key chosen() throws Exception {
        if (store == null) return loaded();
        return store.getKey("g", null);
    }

    private Key plenty;
    void p1() throws Exception { plenty = store.getKey("1", null); }
    void p2() throws Exception { plenty = store.getKey("2", null); }
    void p3() throws Exception { plenty = store.getKey("3", null); }
    void p4() throws Exception { plenty = store.getKey("4", null); }
    void p5() throws Exception { plenty = store.getKey("5", null); }
    void p6() throws Exception { plenty = store.getKey("6", null); }
    void p7() throws Exception { plenty = store.getKey("7", null); }
    void p8() throws Exception { plenty = store.getKey("8", null); }
    void p9() throws Exception { plenty = store.getKey("9", null); }

    byte[] cutPath() throws Exception {
        Mac m = Mac.getInstance("ALG-B"); // site: cut_path
        m.init(helperOfPlenty());
        return m.doFinal(new byte[] {1});
    }

    private Key helperOfPlenty() {
        return plenty;
    }
}
