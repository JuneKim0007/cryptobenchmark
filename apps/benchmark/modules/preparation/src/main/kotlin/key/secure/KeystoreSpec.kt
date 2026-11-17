package io.github.junekim0007.cryptobench.preparation.key.secure

import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.ECGenParameterSpec

/** A KeyGenParameterSpec built by reflection from the guide's keystore block: Android's classes never reach a JVM module's compile classpath. */
internal object KeystoreSpec {

    private const val PACKAGE = "android.security.keystore"
    const val BUILDER = "$PACKAGE.KeyGenParameterSpec\$Builder"
    const val PROPERTIES = "$PACKAGE.KeyProperties"
    const val PURPOSES = "purposes"
    const val CURVE = "curve"
    const val STRONGBOX = "strongbox"

    /** Null on a runtime with Android's keystore classes; else the not_supported line a secure case gets. */
    fun missing(): String? = try {
        Class.forName(BUILDER)
        null
    } catch (absent: ClassNotFoundException) {
        "not_supported: secure needs $PACKAGE (AndroidKeyStore), absent on this runtime"
    }

    // purposes OR'ed from KeyProperties.PURPOSE_<NAME>; curve the ECGenParameterSpec when the entry gives no key spec; every other list set<Name>(String...)
    fun build(alias: String, authorizations: Map<String, Any>, keySize: Int?, parameterSpec: AlgorithmParameterSpec?, backing: String, sdkInt: Int? = null): AlgorithmParameterSpec {
        val builderClass = Class.forName(BUILDER)
        val properties = Class.forName(PROPERTIES)
        val purposes = names(authorizations, PURPOSES).fold(0) { bits, name -> bits or member(sdkInt) { properties.getField("PURPOSE_$name") }.getInt(null) }
        val builder = builderClass.getConstructor(String::class.java, Int::class.javaPrimitiveType).newInstance(alias, purposes)
        for (name in authorizations.keys - setOf(PURPOSES, CURVE)) {
            val strings = names(authorizations, name).toTypedArray()
            call(member(sdkInt) { builderClass.getMethod("set" + name.replaceFirstChar(Char::uppercaseChar), Array<String>::class.java) }, builder, strings)
        }
        keySize?.let { call(member(sdkInt) { builderClass.getMethod("setKeySize", Int::class.javaPrimitiveType) }, builder, it) }
        (parameterSpec ?: authorizations[CURVE]?.let { ECGenParameterSpec(it.toString()) })?.let { call(member(sdkInt) { builderClass.getMethod("setAlgorithmParameterSpec", AlgorithmParameterSpec::class.java) }, builder, it) }
        if (backing == STRONGBOX) call(member(sdkInt) { builderClass.getMethod("setIsStrongBoxBacked", Boolean::class.javaPrimitiveType) }, builder, true)
        return call(builderClass.getMethod("build"), builder) as AlgorithmParameterSpec
    }

    private fun names(authorizations: Map<String, Any>, name: String): List<String> =
        (authorizations[name] as? List<*>)?.map { it.toString() } ?: throw IllegalArgumentException("invalid: guide keystore.$name ${authorizations[name]}, a list of names")

    // a member this API level (the capture's) lacks is api_too_low, never a stack trace
    private fun <T> member(sdkInt: Int?, find: () -> T): T = try {
        find()
    } catch (absent: ReflectiveOperationException) {
        throw AbsentMember("api_too_low: ${absent.message} is absent on API $sdkInt")
    }

    class AbsentMember(reason: String) : UnsupportedOperationException(reason)

    private fun call(method: Method, target: Any, vararg arguments: Any?): Any? = try {
        method.invoke(target, *arguments)
    } catch (thrown: InvocationTargetException) {
        throw thrown.targetException
    }
}
