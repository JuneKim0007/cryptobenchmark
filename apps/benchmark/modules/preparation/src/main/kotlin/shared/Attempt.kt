package io.github.junekim0007.cryptobench.preparation.shared

// The probe's rule (discovery contract/Attempt; no shared module): an Exception or LinkageError is the attempt's result, any other Error ends the run.
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
