# Targets

`apps.targets` resolved to the guide's apps by `app/facts/target_set.py`; each folder's kind by `app/facts/kind.py`. Static only: no model, no build.

## Entries

```yaml
apps:
  targets:                       # inline, or a string: a targets file holding the same list
    - root: ../apps/             # every app under it, depth 4
      perfMode: [latency]        # optional; on a root, every app it finds
    - path: ../other/app         # exactly this folder, also outside every root
    - ../plain/app               # a bare string is a path entry
```

- Relative paths resolve against the file that holds the list: `perfrepair.yaml`'s folder, or the targets file's; the targets file itself is relative to `perfrepair.yaml`'s folder.
- A targets file that is missing is `missing_file`; one that is not a list of entries is `invalid`; template: `targets.example.yaml`.
- A root's candidates are the outermost folders under it that are a project root (`app/facts/roots.py`: settings file, build file beside a source set, legacy Ant) or hold an `AndroidManifest.xml`; `app/find/ignored.yaml` folders are not entered, symlinks not followed, one leaving the root is a warning and the root finds nothing.

## Kinds

| kind | reason | when |
|---|---|---|
| `app` | none | a module build file applies `com.android.application`: `plugins { id("...") }` or `id '...'`, `apply plugin: '...'`, or `alias(libs.plugins.<x>)` whose `gradle/libs.versions.toml` `[plugins]` entry has that id |
| `library` | none | no module applies the application plugin, one applies `com.android.library` in the same forms |
| `app` | `legacy_ant` | no build files; `AndroidManifest.xml` and `project.properties` without `android.library=true` |
| `library` | `legacy_ant` | the same with `android.library=true` |
| `unknown_layout` | `convention_plugin_unresolved` | build files with no Android plugin, and a `plugins {}` block naming another id (a convention plugin of `buildSrc` or `build-logic`) or an alias the catalog lacks |
| `unknown_layout` | `no_android_plugin` | build files with no Android plugin and no other plugin id, beside a manifest (`apply plugin: 'android'`, `com.android.model.application`) |
| `unknown_layout` | `manifest_only` | a manifest and no build files |
| `not_android` | none | none of the above |

- `applicationId` is the first application module's `applicationId "x"` or `applicationId = "x"`, else its manifest's `package=`; comments are not read.
- Under a root only `app` is a target; every other candidate is skipped, its reason its kind's reason or the kind.
- A path entry that is `app` or `library` is a target, labelled with its kind; any other kind, or no folder, is that app's stop: `not_android_project` or `target_missing`, in its `app <id>:` line.

## Merging

- Entries in order; a root's candidates in path order.
- A target whose resolved path, then whose `applicationId`, an earlier target has is skipped `duplicate_of: <that path>`; the earlier entry's `perfMode` stays.
- A root that finds no app is one `warning: apps.targets root <path> holds no app (...)` line.
- Every skipped candidate is one `guide targets: skip <path> <kind>: <reason>` line before the device stage.
- No target at all is the stop `no_targets` before any device or model step.

## `targets.yaml`

Written to `<device>/targets.yaml` by the guide's targets step, after prerequisites and before grouping; `--app` writes none.

| field | holds |
|---|---|
| `schemaVersion` | 1 |
| `apps[]` | `path`, `kind`, `applicationId`, `entry` (`{root: ...}` or `{path: ...}`, the entry that found it), `perfMode` (`null`: `apps.perfMode`) |
| `skipped[]` | `path`, `kind` (or `missing`), `reason`, `entry` |
