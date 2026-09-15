package com.example.cryptobenchmark.environment.discovery;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/** Single source of truth for attribute typing, shared by JCA parsing and JSON writing. */
public enum AttributeKind {
    LIST, INT, BOOL, STRING;

    private static final Map<String, AttributeKind> KINDS;

    static {
        Map<String, AttributeKind> kinds = new HashMap<String, AttributeKind>();
        kinds.put("SupportedModes", LIST);
        kinds.put("SupportedPaddings", LIST);
        kinds.put("SupportedKeyClasses", LIST);
        kinds.put("SupportedKeyFormats", LIST);
        kinds.put("SupportedCurves", LIST);
        kinds.put("KeySize", INT);
        kinds.put("ThreadSafe", BOOL);
        kinds.put("ImplementedIn", STRING);
        kinds.put("MechanismType", STRING);
        KINDS = Collections.unmodifiableMap(kinds);
    }

    public static AttributeKind of(String attribute) {
        AttributeKind kind = KINDS.get(attribute);
        return kind == null ? STRING : kind;
    }

    public static boolean isKnown(String attribute) {
        return KINDS.containsKey(attribute);
    }

    /** @throws NumberFormatException when an INT attribute does not hold a number. */
    public static Object parse(String attribute, String raw) {
        switch (of(attribute)) {
            case LIST:
                return splitPipe(raw);
            case INT:
                return Integer.valueOf(Integer.parseInt(raw.trim()));
            case BOOL:
                return Boolean.valueOf(Boolean.parseBoolean(raw.trim()));
            case STRING:
            default:
                return raw;
        }
    }

    public static List<String> splitPipe(String raw) {
        List<String> parts = new ArrayList<String>();
        if (raw == null) {
            return parts;
        }
        String[] pieces = raw.split("\\|");
        for (int i = 0; i < pieces.length; i++) {
            String trimmed = pieces[i].trim();
            if (!trimmed.isEmpty()) {
                parts.add(trimmed);
            }
        }
        return parts;
    }
}
