package io.github.junekim0007.cryptobench.document

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test

class DocumentFieldsTest {

    @Suppress("UNCHECKED_CAST")
    private val nullValue = mapOf("k" to null) as Map<String, Any>
    private val absent = emptyMap<String, Any>()

    @Test
    fun sectionsIfKeyPresentFailsOnANullValueAndGivesEmptyForAnAbsentKey() {
        val failure = assertThrows(IllegalArgumentException::class.java) { DocumentFields.sectionsIfKeyPresent(nullValue, "k") }
        assertEquals("missing_field: k", failure.message)
        assertEquals(emptyList<Map<String, Any>>(), DocumentFields.sectionsIfKeyPresent(absent, "k"))
    }

    @Test
    fun optionalSectionsGivesEmptyForANullValue() {
        assertEquals(emptyList<Map<String, Any>>(), DocumentFields.optionalSections(nullValue, "k"))
    }

    @Test
    fun optionalSectionIsNullForAnAbsentKeyAndANullValue() {
        assertNull(DocumentFields.optionalSection(absent, "k"))
        assertNull(DocumentFields.optionalSection(nullValue, "k"))
    }

    @Test
    fun sectionOrEmptyIsEmptyForAnAbsentKeyAndANullValue() {
        assertEquals(emptyMap<String, Any>(), DocumentFields.sectionOrEmpty(absent, "k"))
        assertEquals(emptyMap<String, Any>(), DocumentFields.sectionOrEmpty(nullValue, "k"))
    }
}
