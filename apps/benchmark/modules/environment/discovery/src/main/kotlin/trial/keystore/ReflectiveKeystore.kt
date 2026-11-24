package io.github.junekim0007.cryptobench.discovery.trial.keystore

import io.github.junekim0007.cryptobench.contract.trial.KeystoreRow
import io.github.junekim0007.cryptobench.document.names.AlgorithmNames
import io.github.junekim0007.cryptobench.jca.failure.Attempt
import io.github.junekim0007.cryptobench.jca.reflect.Reflect
import java.security.KeyPairGenerator
import java.security.KeyStore
import java.security.Provider
import java.security.spec.AlgorithmParameterSpec
import java.security.spec.ECGenParameterSpec
import javax.crypto.KeyGenerator

/** A KeyGenParameterSpec built by reflection, as preparation's KeystoreSpec builds it: Android's classes never reach a JVM module's compile classpath. */
internal object ReflectiveKeystore : KeystoreMaker {

    private const val PACKAGE = "android.security.keystore"
    private const val BUILDER = "$PACKAGE.KeyGenParameterSpec\$Builder"
    private const val PROPERTIES = "$PACKAGE.KeyProperties"
    private const val PURPOSES = "purposes"
    private const val CURVE = "curve"
    private const val STRONGBOX_FEATURE = "android.hardware.strongbox_keystore"
    private const val KEY_STORE = "KeyStore"
    private val PAIR = AlgorithmNames.fold("KeyPairGenerator")

    override fun missing(): String? = try {
        Class.forName(BUILDER)
        null
    } catch (absent: ClassNotFoundException) {
        "not_supported: the keystore trial needs $PACKAGE (AndroidKeyStore), absent on this runtime"
    }

    override fun strongBox(): Boolean? = Attempt.of {
        val application = Class.forName("android.app.ActivityThread").getMethod("currentApplication").invoke(null) ?: return null
        val packages = application.javaClass.getMethod("getPackageManager").invoke(application)
        packages.javaClass.getMethod("hasSystemFeature", String::class.java).invoke(packages, STRONGBOX_FEATURE) as Boolean
    }.getOrNull()

    override fun generate(provider: Provider, request: KeystoreRequest, alias: String, sdkInt: Int) {
        val spec = spec(alias, request, sdkInt)
        if (AlgorithmNames.fold(request.type) == PAIR) {
            KeyPairGenerator.getInstance(request.algorithm, provider).apply { initialize(spec) }.generateKeyPair()
        } else {
            KeyGenerator.getInstance(request.algorithm, provider).apply { init(spec) }.generateKey()
        }
    }

    override fun sweep(provider: Provider, prefix: String) {
        val store = store(provider)
        store.aliases().toList().filter { it.startsWith(prefix) }.forEach(store::deleteEntry)
    }

    override fun delete(provider: Provider, alias: String) {
        store(provider).deleteEntry(alias)
    }

    private fun store(provider: Provider): KeyStore {
        val type = provider.services.firstOrNull { it.type == KEY_STORE }?.algorithm ?: throw IllegalStateException("not_supported: ${provider.name} registers no $KEY_STORE")
        return KeyStore.getInstance(type, provider).apply { load(null) }
    }

    // purposes OR'ed from KeyProperties.PURPOSE_<NAME>; the request's curve, else the block's; every other list set<Name>(String...)
    private fun spec(alias: String, request: KeystoreRequest, sdkInt: Int): AlgorithmParameterSpec {
        val builderClass = Class.forName(BUILDER)
        val properties = Class.forName(PROPERTIES)
        val authorizations = request.authorizations
        val purposes = names(authorizations, PURPOSES).fold(0) { bits, name -> bits or member(sdkInt) { properties.getField("PURPOSE_$name") }.getInt(null) }
        val builder = builderClass.getConstructor(String::class.java, Int::class.javaPrimitiveType).newInstance(alias, purposes)
        for (name in authorizations.keys - setOf(PURPOSES, CURVE)) {
            val strings = names(authorizations, name).toTypedArray()
            Reflect.invoke(member(sdkInt) { builderClass.getMethod("set" + name.replaceFirstChar(Char::uppercaseChar), Array<String>::class.java) }, builder, strings)
        }
        request.keySize?.let { Reflect.invoke(member(sdkInt) { builderClass.getMethod("setKeySize", Int::class.javaPrimitiveType) }, builder, it) }
        (request.curve.ifEmpty { authorizations[CURVE]?.toString().orEmpty() }).takeIf { it.isNotEmpty() }?.let {
            Reflect.invoke(member(sdkInt) { builderClass.getMethod("setAlgorithmParameterSpec", AlgorithmParameterSpec::class.java) }, builder, ECGenParameterSpec(it))
        }
        if (request.backing == KeystoreRow.STRONGBOX) Reflect.invoke(member(sdkInt) { builderClass.getMethod("setIsStrongBoxBacked", Boolean::class.javaPrimitiveType) }, builder, true)
        return Reflect.invoke(builderClass.getMethod("build"), builder) as AlgorithmParameterSpec
    }

    private fun names(authorizations: Map<String, Any>, name: String): List<String> =
        (authorizations[name] as? List<*>)?.map { it.toString() } ?: throw IllegalArgumentException("invalid: catalogue keystore.$name ${authorizations[name]}, a list of names")

    private fun <T> member(sdkInt: Int, find: () -> T): T = try {
        find()
    } catch (absent: ReflectiveOperationException) {
        throw KeystoreMaker.AbsentMember("api_too_low: ${absent.message} is absent on API $sdkInt")
    }
}
