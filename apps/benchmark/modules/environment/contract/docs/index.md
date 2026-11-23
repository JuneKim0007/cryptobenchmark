# contract

```
apps/benchmark/modules/environment/contract/README.md : module summary and link to this index
apps/benchmark/modules/environment/contract/build.gradle : Kotlin/JVM 17 library; :document only; no :jca
apps/benchmark/modules/environment/contract/docs/index.md : this map
apps/benchmark/modules/environment/contract/src/main/kotlin/Handoff.kt : a capture with the trial (and requirements) written with it: read through the readers, paired by capturedAtMillis, mismatched_trial refused
apps/benchmark/modules/environment/contract/src/main/kotlin/bundled/BundledProvider.kt : one providers.bundled entry and its rule: artifact group:name:version, create Class or Class#factory, alias without whitespace; className and factory
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/CaptureDocument.kt : capture YAML schema (of) and its one reader (DocumentReader parse; read: VersionedFile on the DOCUMENT codec)
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/CapturedEnvironment.kt : capture model, SCHEMA_VERSION 1; providers listed in ascending, unique precedence, else invalid
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/ProviderEntry.kt : one provider record with origin and artifact
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/ProviderOrigin.kt : platform or bundled
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/RuntimeDocument.kt : the capture's runtime section: its 12 key names, of and parse, and host: the 6 a host benchmark.json carries; CaptureDocument and config's CaptureView use it
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/RuntimeInfo.kt : device and runtime provenance
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/ServiceAttributes.kt : typed view of a service's declared attributes
apps/benchmark/modules/environment/contract/src/main/kotlin/capture/ServiceEntry.kt : one service record
apps/benchmark/modules/environment/contract/src/main/kotlin/requirements/KeyCacheStats.kt : keys generated, refused and reused over a run
apps/benchmark/modules/environment/contract/src/main/kotlin/requirements/RequirementDocument.kt : requirements YAML schema (of, header, serviceDocument) and its one reader (DocumentReader parse; read: VersionedFile on the DOCUMENT codec)
apps/benchmark/modules/environment/contract/src/main/kotlin/requirements/RequirementReport.kt : requirements model, SCHEMA_VERSION 1
apps/benchmark/modules/environment/contract/src/main/kotlin/requirements/ServiceRequirement.kt : one service's requirements record and its reason codes
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/DefaultRunOutcome.kt : one default-run result
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/KeystoreSection.kt : keystore trial rows (one generation per size or curve and path) or the reason the section is absent
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/ServiceTrialEntry.kt : trial result for one service
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/TransformationTrialEntry.kt : trial result for one cipher transformation
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/TrialDocument.kt : trial YAML schema (of) and its one reader (DocumentReader parse; read: VersionedFile on the DOCUMENT codec)
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/TrialOutcome.kt : instantiation success or error
apps/benchmark/modules/environment/contract/src/main/kotlin/trial/TrialReport.kt : trial model, SCHEMA_VERSION 3
```
