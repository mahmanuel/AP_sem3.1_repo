# Automated Review and Final Design Evaluation

This report records the automated review for Questions 3 and 4. It separates
findings confirmed by completed scans from checks that could not be completed
in this environment.

## Question 3 — Automated review tools

### Code quality: SonarLint / SonarQube for IDE

- **Tool/version:** SonarQube for IDE (SonarLint) 6.2.0, with its bundled PHP
  analyzer; VS Code 1.144.0 and bundled Java 21.
- **Configuration and scope:** Local IDE analysis using the analyzer's active
  PHP rules, without a connected SonarQube server or custom rule set. The
  reviewed scope was `generate_qrcodes.php` and
  `tests/generate_qrcodes_test.php`.
- **Initial result:** The completed pre-fix analysis reported 18 diagnostics:

  | File | Rule | Count | Finding |
  |---|---|---:|---|
  | `generate_qrcodes.php` | `php:S2003` | 1 | Prefer `require_once` to `require`. |
  | `generate_qrcodes.php` | `php:S112` | 7 | Avoid throwing generic exceptions. |
  | `generate_qrcodes.php` | `php:S3776` | 1 | Reduce cognitive complexity (reported value 17; threshold 15). |
  | `tests/generate_qrcodes_test.php` | `php:S2003` | 1 | Prefer `require_once` to `require`. |
  | `tests/generate_qrcodes_test.php` | `php:S112` | 5 | Avoid throwing generic exceptions. |
  | `tests/generate_qrcodes_test.php` | `php:S1192` | 2 | Extract repeated string literals into constants. |
  | `tests/generate_qrcodes_test.php` | `php:S1186` | 1 | The fake renderer's method has an empty body. |

- **Assessment and disposition:** The include, generic-exception, complexity,
  and duplicated-literal findings were valid and addressed. The fake renderer
  intentionally writes no output to test contract enforcement; it remains
  empty with an explanatory comment so the test behavior is clear.
- **Changes made:** Replaced the includes with `require_once`; introduced
  specific generation, output-directory, renderer-contract, and test
  exceptions; extracted temporary-file handling into helpers; reduced the
  generation method's branching; and extracted repeated test literals into
  constants.
- **Repeat scan / comparison:** A post-fix scan was attempted, but the
  SonarLint extension host/backend did not complete analysis reliably in this
  environment. No completed after-scan results are available. The changes
  above target the valid findings, but a zero-issue result is **not claimed**;
  repeat the scan in a stable VS Code session to verify the result.

### Dependency security: OSV vulnerability database

- **Tool/service:** OSV API.
- **Query date:** 2026-11-02.
- **Configuration and scope:** Queried every package and exact version in
  `composer.lock` using the Packagist ecosystem:
  `bacon/bacon-qr-code` v3.0.1, `dasprid/enum` 1.0.6, and
  `endroid/qr-code` 6.0.8.
- **Result:** Zero advisories were returned for each of the three locked
  packages at query time.
- **Assessment:** No dependency vulnerability fix was indicated by this
  query. This does not rule out undisclosed or later-reported vulnerabilities.

### Syntax and functional test status

A PHP 8.2 syntax parser successfully parsed both changed PHP files. This is a
syntax check only; it is not PHP runtime execution. The PHP CLI is unavailable
in this environment, so PHP's own lint and `tests/generate_qrcodes_test.php`
could not be run. The PNG integration test also requires PHP's GD extension.
Run the following in an environment with PHP 8.2+, Composer dependencies, and
GD:

```sh
php -l generate_qrcodes.php
php -l tests/generate_qrcodes_test.php
php tests/generate_qrcodes_test.php
```

## Question 4 — Final design evaluation

### Issue and course principle

The prior implementation checked the destination file after rendering. If an
earlier run had left a non-empty file there, a renderer that produced no new
output could appear to have succeeded. This is a reliability and contract
issue related to the Liskov Substitution Principle: every renderer must meet
the output behavior the caller depends on.

### Improvement and effect

The generator now renders each QR code to a unique temporary file in the
destination directory. It verifies that the new file exists and is non-empty
before renaming it into place. On rendering or validation failure, it removes
the temporary file and preserves any prior destination. The output directory
is requested with mode `0755`, rather than `0777`.

The standalone tests now cover successful replacement, preservation of a
previous output after a renderer fails or omits output, and temporary-file
cleanup. These tests are present but their execution remains pending because
PHP/GD are unavailable in this environment.

### Before-and-after summary

| Area | Before | After / verification status |
|---|---|---|
| SonarLint findings | 18 pre-fix diagnostics across the two reviewed PHP files. | Corresponding changes were made for valid findings. A completed post-fix scan is unavailable, so the final count is unverified. |
| Failed rendering with stale output | An old non-empty output could satisfy the final-file check. | New output is validated in a temporary file before replacement; failure preserves the old file. |
| Requested directory mode | `0777`. | `0755`. |
| Locked dependencies | No recorded automated audit. | OSV returned zero advisories for the three locked package versions at query time. |
| PHP behavior tests | No tests covering failure preservation and temporary cleanup. | Tests were added; execution is pending PHP/GD availability. |
| Syntax | Not recorded. | Both files parsed with a PHP 8.2 syntax parser; PHP's own lint remains pending. |

### Remaining limitations and next steps

- Complete a SonarLint scan of both files in a stable IDE session and record
  its final diagnostics, including any remaining issues.
- Run PHP lint and the standalone test script with PHP 8.2+ and GD installed.
- Generation remains sequential and processes 10,000 codes by default. No
  performance benchmark was run, so parallelism or caching changes are not
  justified by measured evidence.
- The batch is not all-or-nothing: files completed before a later failure
  remain, though each individual destination is replaced only after its new
  render passes validation. A future improvement could add resumable batches
  or a manifest.

