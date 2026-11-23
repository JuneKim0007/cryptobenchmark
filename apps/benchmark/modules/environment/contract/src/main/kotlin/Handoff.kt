package io.github.junekim0007.cryptobench.contract

import io.github.junekim0007.cryptobench.contract.capture.CaptureDocument
import io.github.junekim0007.cryptobench.contract.capture.CapturedEnvironment
import io.github.junekim0007.cryptobench.contract.requirements.RequirementReport
import io.github.junekim0007.cryptobench.contract.trial.TrialDocument
import io.github.junekim0007.cryptobench.contract.trial.TrialReport
import java.io.File

/** A capture with the trial, and the requirements when read, that discovery wrote with it. */
class Handoff(val capture: CapturedEnvironment, val trial: TrialReport, val requirements: RequirementReport? = null) {

    // written with the capture: each carries the capture's capturedAtMillis
    fun paired(): Boolean = listOfNotNull(trial.capturedAtMillis, requirements?.capturedAtMillis).all { it == capture.capturedAtMillis }

    companion object {
        fun read(captureFile: File, trialFile: File): Handoff =
            Handoff(CaptureDocument.read(captureFile), TrialDocument.read(trialFile)).apply {
                require(paired()) { "mismatched_trial: capture ${capture.capturedAtMillis}, trial ${trial.capturedAtMillis}" }
            }
    }
}
