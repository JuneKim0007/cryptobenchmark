# Devices

## Listing

`pipeline.py --devices`: `adb devices -l`, then `adb -s <serial> shell getprop` per transport in state `device`; `lib/cryptobench/cryptobench/shared/device/probe.py`. Honours `ANDROID_ADB_SERVER_PORT`.

| column | holds |
|---|---|
| `key` | `ro.serialno` on a physical device; `emulator:<avd>` (`ro.boot.qemu.avd_name`, else `ro.kernel.qemu.avd_name`) on an emulator; the transport serial when neither can be trusted |
| `alias` | from `~/.config/cryptobench/devices.yaml` |
| `kind`, `model`, `api`, `connection` | `physical` or `emulator`; `ro.product.model`; `ro.build.version.sdk`; `usb`, `tcp` or `emulator` |
| `state` | `ready` or the code below |

| adb state or reading | code |
|---|---|
| `unauthorized`, `authorizing` | `device_unauthorized` |
| `offline`, `connecting`, or no answer to `getprop` | `device_offline` |
| `no permissions` | `device_no_permissions` |
| any other state, or `sys.boot_completed` not `1` | `device_not_booted` |
| `ro.serialno` blank or `unknown`, an emulator without an AVD name, or one key on two ready transports | `unstable_id` note: keyed by the transport serial, never resumed |
| nothing listed | `warning: no_device: ...`, exit 0 |
| `adb devices -l` fails | `device_lost: ...` when adb names a lost transport, else `adb devices -l: <message>`; exit 1 |

Each reason and note follows the table as one line with its fix.

`~/.config/cryptobench/devices.yaml`: `schemaVersion: 1`, `aliases: {<alias>: <key>}`; absent is no aliases. An alias or key that is not non-blank text, or an alias with `:`, is `invalid_alias`; two aliases for one key `duplicate_alias`; another top key `unknown_keys`.
