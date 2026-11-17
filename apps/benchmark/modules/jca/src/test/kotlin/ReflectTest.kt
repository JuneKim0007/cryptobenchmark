package io.github.junekim0007.cryptobench.jca

import io.github.junekim0007.cryptobench.jca.reflect.Reflect
import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class ReflectTest {

    class Target {
        fun twice(value: Int): Int = value * 2
        fun refuse(): Nothing = throw IllegalStateException("refused")
    }

    @Test
    fun aCallReturnsTheMethodsValue() {
        assertEquals(6, Reflect.invoke(Target::class.java.getMethod("twice", Int::class.javaPrimitiveType), Target(), 3))
    }

    @Test
    fun aThrowingMethodThrowsItsOwnException() {
        val thrown = assertThrows(IllegalStateException::class.java) { Reflect.invoke(Target::class.java.getMethod("refuse"), Target()) }
        assertEquals("refused", thrown.message)
    }
}
