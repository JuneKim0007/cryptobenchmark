package io.github.junekim0007.cryptobench.files

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class StampedNameTest {
    private val name = StampedName.of(StampedName.PROBE, 1_000L)

    @Test fun formatsTheCaptureMoment() = assertEquals("probe_19700101T000001Z.yaml", name)

    @Test fun recognisesOnlyItsOwnPrefix() {
        assertTrue(StampedName.isStamped(StampedName.PROBE, name))
        assertFalse(StampedName.isStamped(StampedName.TRIAL, name))
        assertFalse(StampedName.isStamped(StampedName.PROBE, "probe_later.yaml"))
    }

    @Test fun pairsAnotherPrefixByTheStamp() = assertEquals("trial_19700101T000001Z.yaml", StampedName.sibling(StampedName.TRIAL, name))

    @Test fun readsTheStamp() {
        assertEquals("19700101T000001Z", StampedName.stampOf(name))
        assertNull(StampedName.stampOf("hand-named.yaml"))
    }
}
