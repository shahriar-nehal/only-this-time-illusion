# only-this-time-illusion
This anonymous repository contains the artifacts required to reproduce the core contributions, measurements, and mitigations presented in our ACM CCS submission. 

In compliance with the double-blind review process, all identifying information (e.g., author names, institutional affiliations, commit histories) has been stripped from this repository. 

## 📁 Repository Structure

    .
    ├── AOSP Mitigation Patch/
    │   └── OneTimePermissionUserManager.java
    ├── Evaluation Dataset/
    │   └── Final_Vulnerable_Dataset.csv
    ├── LocationApplication/
    │   └── LocationApplication/ (Android Studio Project)
    └── Measurement and Analysis Scripts/
        ├── Scanner_Script_Final.py
        └── Analysis_Script.py

---

## 🛠️ Components & Usage Instructions

### 1. Proof-of-Concept (PoC) Application
**Location:** `/LocationApplication/`

This folder contains the full Android Studio source code for the experimental applications developed to systematically trigger the BLIND attack. 

**To run the PoC:**
1. Import the `LocationApplication` folder into Android Studio (Giraffe or newer).
2. Build the `.apk` and deploy it to an Android emulator or physical device running Android Version 13+.
3. Grant the "Only this time" location permission, then swipe the application away from the Recents menu to observe the persistent invisible service state.

### 2. Measurement and Analysis Scripts
**Location:** `/Measurement and Analysis Scripts/`

These scripts replicate our automated pipeline for tracking the Invisible State via `adb` and extracting metadata from our compiled dataset.

* **Prerequisites:** Requires Python 3.8+, an active `adb` connection to a **rooted Android device or emulator** (root access is strictly required for the scanner to accurately hook into system-level service states), and the following libraries:
    ```bash
    pip install pandas numpy
    ```
* `Scanner_Script_Final.py`: The dynamic measurement engine. It utilizes privileged `adb shell dumpsys activity services` commands on the rooted device to actively poll the foreground service (`fgsvc`) state of target applications. It measures the exact duration applications survive post-UI dismissal and outputs the survival traces to `results_events.csv`.
* `Analysis_Script.py`: The static dataset parser. It processes the finalized vulnerable dataset to calculate the ecosystem impact, including Target SDK distributions, permission omission rates (e.g., Background Location vs. Fine Location), and the prevalence of embedded telemetry frameworks like Google Location and Firebase Analytics.

### 3. Evaluation Dataset
**Location:** `/Evaluation Dataset/`

* `Final_Vulnerable_Dataset.csv`: Contains the finalized 98 apps' structured data from our ecosystem measurement. Due to anonymous hosting constraints and file size limits (>1 GB), the raw commercial `.apk` binaries are not included. This dataset provides `App Name`, `Category`, `Installs`, `Rating`, `Target_SDK`, `Has_Fine_Loc`, `Has_Background_Loc`, `Has_Post_Notif`, `Declared_FGS_Types`, and `Embedded_Trackers` required to independently verify our findings.

### 4. AOSP Mitigation Patch
**Location:** `/AOSP Mitigation Patch/`

* `OneTimePermissionUserManager.java`: This file contains our proposed security mitigation for the Android Open Source Project (AOSP). It modifies the `OneTimePermissionUserManager` logic to enforce a strict validation check, ensuring that foreground services are correctly revoked if they fail to materialize a visible UI notification within the 5-second grace period.
* **To inspect:** Review the patched logic alongside the standard AOSP 13/14 branch to observe the corrected state-mismatch handling.

---

## 📝 Note to Reviewers
These artifacts are provided exclusively for the purpose of evaluating this paper during the ACM CCS review cycle. The repository is hosted anonymously to prevent access tracking. Upon acceptance, we will release all source code, datasets, and scripts under an open-source license on a permanent, citable platform and register for the optional Artifact Evaluation (AE) process.
