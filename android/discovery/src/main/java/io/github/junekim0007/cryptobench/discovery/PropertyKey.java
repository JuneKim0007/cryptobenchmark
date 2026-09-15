package io.github.junekim0007.cryptobench.discovery;

/** Every Provider property-map trap lives here: the Provider.id namespace, aliases, and attributes. */
final class PropertyKey {

    enum Kind { PROVIDER_META, ALIAS, ATTRIBUTE, SERVICE_IMPL, MALFORMED }

    private static final String META_PREFIX = "Provider.";
    private static final String ALIAS_PREFIX = "Alg.Alias.";

    private final Kind kind;
    private final String type;
    private final String algorithm;
    private final String attribute;

    private PropertyKey(Kind kind, String type, String algorithm, String attribute) {
        this.kind = kind;
        this.type = type;
        this.algorithm = algorithm;
        this.attribute = attribute;
    }

    /**
     * Classifies one raw key of the provider property map.
     *
     * <pre>
     * "Provider.id name"          -> PROVIDER_META  (never a service type)
     * "Alg.Alias.Cipher.RC4"      -> ALIAS          type=Cipher, attribute=RC4, value=target
     * "Cipher.AES SupportedModes" -> ATTRIBUTE      type=Cipher, algorithm=AES
     * "Cipher.AES"                -> SERVICE_IMPL
     * </pre>
     */
    public static PropertyKey classify(String key) {
        if (key == null) {
            return malformed();
        }
        if (key.startsWith(META_PREFIX)) {
            return new PropertyKey(Kind.PROVIDER_META, null, null, null);
        }
        if (key.startsWith(ALIAS_PREFIX)) {
            String rest = key.substring(ALIAS_PREFIX.length());
            int dot = rest.indexOf('.');
            if (dot <= 0 || dot == rest.length() - 1) {
                return malformed();
            }
            return new PropertyKey(Kind.ALIAS, rest.substring(0, dot), null, rest.substring(dot + 1));
        }
        int space = key.indexOf(' ');
        if (space < 0) {
            return split(Kind.SERVICE_IMPL, key, null);
        }
        return split(Kind.ATTRIBUTE, key.substring(0, space), key.substring(space + 1).trim());
    }

    private static PropertyKey split(Kind kind, String head, String attribute) {
        int dot = head.indexOf('.');
        if (dot <= 0 || dot == head.length() - 1) {
            return malformed();
        }
        if (kind == Kind.ATTRIBUTE && (attribute == null || attribute.isEmpty())) {
            return malformed();
        }
        return new PropertyKey(kind, head.substring(0, dot), head.substring(dot + 1), attribute);
    }

    private static PropertyKey malformed() {
        return new PropertyKey(Kind.MALFORMED, null, null, null);
    }

    public Kind getKind() {
        return kind;
    }

    public String getType() {
        return type;
    }

    public String getAlgorithm() {
        return algorithm;
    }

    public String getAttribute() {
        return attribute;
    }

    public ServiceKey serviceKey() {
        return ServiceKey.of(type, algorithm);
    }
}
