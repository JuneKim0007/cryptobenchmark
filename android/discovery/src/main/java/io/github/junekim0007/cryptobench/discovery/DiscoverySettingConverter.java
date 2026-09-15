package io.github.junekim0007.cryptobench.discovery;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collection;
import java.util.Collections;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Reduces a full capture to the discovery setting. Typed to typed: it never reads a file or a field
 * name, so serialization changes cannot break it. Every field it drops is listed in
 * security_contract.md under "cropped".
 */
public final class DiscoverySettingConverter {

    /** Service types the benchmark measures. Everything else in a capture is cropped. */
    public static final Set<String> BENCHMARKED_TYPES = Collections.unmodifiableSet(
            new LinkedHashSet<String>(Arrays.asList(
                    "Cipher", "MessageDigest", "Mac", "Signature",
                    "KeyGenerator", "KeyPairGenerator", "KeyAgreement")));

    private final Set<String> types;

    public DiscoverySettingConverter() {
        this(BENCHMARKED_TYPES);
    }

    /** Scope is a parameter so it can come from configuration rather than this constant. */
    public DiscoverySettingConverter(Collection<String> types) {
        Set<String> folded = new HashSet<String>();
        if (types != null) {
            for (String type : types) {
                if (type != null) {
                    folded.add(ServiceKey.fold(type));
                }
            }
        }
        this.types = Collections.unmodifiableSet(folded);
    }

    public DiscoverySetting convert(CapturedEnvironment capture) {
        if (capture == null) {
            throw new NullPointerException("capture");
        }
        RuntimeInfo runtime = capture.getRuntime();
        DiscoverySetting.Device device = new DiscoverySetting.Device(
                runtime.getModel(),
                runtime.getManufacturer(),
                runtime.getHardware(),
                runtime.getSdkInt(),
                runtime.getRelease());

        List<DiscoverySetting.ProviderSetting> providers = new ArrayList<DiscoverySetting.ProviderSetting>();
        for (ProviderEntry provider : capture.getProviders()) {
            providers.add(new DiscoverySetting.ProviderSetting(
                    provider.getName(),
                    provider.getVersion(),
                    provider.getPrecedence(),
                    inScope(provider.getServices())));
        }
        return new DiscoverySetting(capture.getCapturedAtMillis(), device, providers);
    }

    private List<DiscoverySetting.ServiceSetting> inScope(List<ServiceEntry> services) {
        List<DiscoverySetting.ServiceSetting> kept = new ArrayList<DiscoverySetting.ServiceSetting>();
        for (ServiceEntry service : services) {
            if (!types.contains(ServiceKey.fold(service.getType()))) {
                continue;
            }
            ServiceAttributes attributes = service.getAttributes();
            kept.add(new DiscoverySetting.ServiceSetting(
                    service.getType(),
                    service.getAlgorithm(),
                    service.getAliases(),
                    attributes.supportedModes(),
                    attributes.supportedPaddings(),
                    attributes.keySize()));
        }
        return kept;
    }
}
