package io.github.junekim0007.cryptobench.discovery.contract

// A provider's Exception or LinkageError (a class it was built against is missing) is the attempt's result; any other Error, OOM first, ends the probe.
internal object Attempt {

    inline fun <T> of(block: () -> T): Result<T> =
        try {
            Result.success(block())
        } catch (exception: Exception) {
            Result.failure(exception)
        } catch (linkageError: LinkageError) {
            Result.failure(linkageError)
        }
}
