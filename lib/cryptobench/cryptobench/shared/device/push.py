"""A device run's plan pushed to the device, the suppressErrors warning after it, then the energy settle's files."""


def push(device, options, plan, energy=None):
    """dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle."""
    device.push_plan(*plan)
    if options.suppress_errors:
        print(f"warning: suppressErrors {options.suppress_errors}: these numbers are not comparable to an unsuppressed run")
    if energy:
        device.push_files(energy())
