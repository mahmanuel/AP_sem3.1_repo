# SOLID Refactoring Notes

This document records the code review and refactoring work on the QR code
generator, organized by the five SOLID principles. The refactor keeps the
existing command-line behavior: running `generate_qrcodes.php` directly
generates 10,000 labeled PNG files named `qr_00001.png` through
`qr_10000.png` in the `qrcodes/` directory.

## Starting point and issue

The project is a small PHP command-line QR code generator using
`endroid/qr-code`. Initially, the script configured each QR code, generated it,
prepared the output filename, and saved the result inside the same loop. It
also attempted to create the output directory without checking whether
creation succeeded or whether the directory was writable.

The refactoring separated QR rendering from batch coordination, made the
renderer replaceable through an interface, and added checks for invalid output
paths and incomplete renderers.

## S — Single Responsibility Principle

**Principle:** A module should have one primary responsibility, and therefore
one main reason to change.

**Before:** The batch loop in `generate_qrcodes.php` was responsible for
numbering codes, configuring the QR library, building QR images, constructing
paths, and saving files. A change to QR appearance and a change to batch
output behavior both required editing the same loop.

**Refactor:** QR-specific configuration and rendering are now in
`PngQrCodeRenderer`. `generateQrCodes()` handles batch coordination: it
validates the count, prepares the output directory, formats each number,
constructs the output path, and delegates rendering. Directory setup remains
in the separate `ensureOutputDirectory()` function.

**Why it helps:** QR appearance can change independently of batch sequencing
and output naming. Output setup can be maintained separately from QR-library
configuration.

## O — Open/Closed Principle

**Principle:** Software should be open for extension but closed for
modification: new behavior should usually be added without modifying stable
existing logic.

**Before:** The generation loop created PNGs directly and used the `.png`
extension as part of its own file-saving logic. Supporting another renderer
would require editing the loop.

**Refactor:** A `QrCodeRenderer` interface defines `fileExtension()` and
`render()`. `PngQrCodeRenderer` implements it. The generator uses the supplied
renderer for each item, so another renderer can be added without changing the
batch loop. The CLI currently supplies the PNG implementation.

**Why it helps:** New output implementations can be introduced independently
of the batch workflow.

## L — Liskov Substitution Principle

**Principle:** An implementation of an abstraction should be usable wherever
that abstraction is expected without breaking the caller's expectations.

**Contract and checks:** `QrCodeRenderer` documents that the extension is
returned without a leading dot and that rendering writes a non-empty file to
the requested path. Before generation, the generator rejects extensions that
are empty or contain characters outside letters and digits. After each render,
it checks that the requested path exists as a file and is non-empty. If those
expectations are not met, generation stops with a clear `RuntimeException`.

**Why it helps:** An alternate renderer cannot silently produce missing or
empty output that appears to be a successful run.

## I — Interface Segregation Principle

**Principle:** Clients and implementations should not be forced to depend on
interface methods they do not use.

**Review outcome:** `QrCodeRenderer` has two closely related methods: the
extension used to name output files and the rendering operation that creates
those files. The generator needs both, and renderer implementations provide
both. No ISP refactor was necessary.

**Why no change was made:** Splitting this small, cohesive interface would
create additional abstractions without giving current clients a more focused
dependency.

## D — Dependency Inversion Principle

**Principle:** High-level policy should depend on abstractions rather than
concrete implementation details. Concrete choices should be supplied from the
outside.

**Before:** The generator could choose a concrete PNG renderer as a fallback
when no renderer was passed. This left the batch workflow responsible for
choosing its rendering implementation.

**Refactor:** `generateQrCodes()` now requires a `QrCodeRenderer` argument.
The command-line entry point constructs and supplies `PngQrCodeRenderer`.
Thus, the batch process depends on the renderer abstraction, while the
application entry point chooses the concrete PNG implementation.

**Why it helps:** Callers can select a different renderer without changing the
batch-generation logic. The CLI's existing default remains PNG.

## Error handling and input validation

These changes support the refactor and improve reliability:

- The generator rejects a count below one with `InvalidArgumentException`.
- `ensureOutputDirectory()` rejects a path that exists but is not a directory,
  reports a directory-creation failure, and rejects a directory that is not
  writable.
- The renderer extension is validated before it is used in a filename.
- The generator raises an explicit error if a renderer does not create a
  non-empty output file.

## Tests and verification

`tests/generate_qrcodes_test.php` exercises the following:

- PNG generation for a small batch, checking expected filenames and the PNG
  file signature.
- Injection of a simple test renderer, checking that it controls the
  extension and output content.
- A renderer that does not create a file, checking that the generator reports
  the violated output contract.
- An output path that is a regular file, checking that directory validation
  reports a clear error.

The test file is a standalone PHP script; no test framework or test command is
configured in `composer.json`. The intended invocation is:

```sh
php -l generate_qrcodes.php
php -l tests/generate_qrcodes_test.php
php tests/generate_qrcodes_test.php
```

These commands could not be run in the development environment because the PHP
CLI was not installed (`php: command not found`). Consequently, the tests are
present but their execution has not been verified here.
