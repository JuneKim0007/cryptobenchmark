package io.github.junekim0007.cryptobench.files

import org.junit.Assert.assertEquals
import org.junit.Test
import java.io.File

class BesideTest {
    private val anchor = File("/a/b/effective.yaml")

    @Test fun inTheAnchorsFolder() = assertEquals(File("/a/b/guide.yaml"), Beside.file(anchor, "guide.yaml"))

    @Test fun anAbsoluteValueStands() = assertEquals(File("/c/set.yaml"), Beside.authored(anchor, "/c/set.yaml"))

    @Test fun aRelativeValueIsBesideTheFile() = assertEquals(File("/a/b/set.yaml"), Beside.authored(anchor, "set.yaml"))
}
