package io.github.junekim0007.cryptobench.discovery.bundled

import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Modifier
import java.security.Provider

class ProviderFactory(private val classLoader: ClassLoader) {

    fun create(spec: BundledProvider): Provider {
        val type = try {
            Class.forName(spec.className, true, classLoader)
        } catch (missing: ClassNotFoundException) {
            throw BundledProviderException("bundled_class_not_found", "${spec.className} (${spec.artifact})", missing)
        }
        val made = try {
            spec.factory?.let { invokeFactory(type, it, spec) } ?: type.getDeclaredConstructor().newInstance()
        } catch (missing: NoSuchMethodException) {
            throw BundledProviderException("bundled_factory_not_found", "${spec.create} has no public no-argument ${spec.factory ?: "constructor"}", missing)
        } catch (failed: InvocationTargetException) {
            throw BundledProviderException("bundled_create_failed", "${spec.create}: ${failed.targetException}", failed.targetException)
        } catch (failed: ReflectiveOperationException) {
            throw BundledProviderException("bundled_create_failed", "${spec.create}: $failed", failed)
        } catch (failed: LinkageError) {
            throw BundledProviderException("bundled_create_failed", "${spec.create}: $failed", failed)
        }
        return made as? Provider ?: throw BundledProviderException("bundled_not_a_provider", "${spec.create} made ${made?.javaClass?.name}")
    }

    private fun invokeFactory(type: Class<*>, name: String, spec: BundledProvider): Any? {
        val method = type.getMethod(name)
        if (!Modifier.isStatic(method.modifiers)) throw BundledProviderException("bundled_factory_not_static", spec.create)
        return method.invoke(null)
    }
}
