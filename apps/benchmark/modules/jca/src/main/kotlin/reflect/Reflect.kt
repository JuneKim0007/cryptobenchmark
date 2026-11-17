package io.github.junekim0007.cryptobench.jca.reflect

import java.lang.reflect.InvocationTargetException
import java.lang.reflect.Method

object Reflect {

    // What the called method threw, never its InvocationTargetException wrapper.
    fun invoke(method: Method, target: Any?, vararg arguments: Any?): Any? = try {
        method.invoke(target, *arguments)
    } catch (thrown: InvocationTargetException) {
        throw thrown.targetException
    }
}
