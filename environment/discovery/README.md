# Discovery

> An independent module designed to discover available settings and device capabilities within scope.

## Responsibilities

- Discovery is responsible for identifying available cryptography providers.

  1. For more information, refer to <probe.md>.

## File Structure

- `Discovery/`: Main root repository of the `Discovery` module
  - `src/main/kotlin/`: Discovery modules written in Kotlin
    - `probe/`: Directory responsible for probing available cryptography providers registered in Java.

## Limitations

- The `Probe` module primarily uses the Java Security library, particularly `java.security.Provider`, making it highly dependent on the Java Security API.
- `Probe` only searches for cryptography providers registered in Java. Unregistered cryptography algorithms and pr
