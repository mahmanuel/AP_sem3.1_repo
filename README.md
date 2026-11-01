# AP_sem3.1_repo


# QR Code Wizard

A PHP command-line tool that generates numbered QR code PNG images using
[`endroid/qr-code`](https://github.com/endroid/qr-code).

## Requirements

- PHP 8.2 or newer
- Composer
- PHP GD extension (used by the PNG writer)

## Installation

From the project directory, install the locked Composer dependencies:

```sh
composer install
```

## Generate QR codes

Run the generator from the project directory:

```sh
php generate_qrcodes.php
```

The script creates a `qrcodes/` directory if needed and generates 10,000 PNG
files:

```text
qrcodes/
├── qr_00001.png
├── qr_00002.png
└── ...
└── qr_10000.png
```

Each QR code contains its five-digit number and displays the same number as a
label. The current configuration uses high error correction, a 300-pixel size,
a margin of 10, and a 16-point Open Sans label.

Generated files are ignored by Git via `.gitignore`.

## Tests

The repository includes a standalone PHP test script. Run it with:

```sh
php -l generate_qrcodes.php
php -l tests/generate_qrcodes_test.php
php tests/generate_qrcodes_test.php
```

The test script checks PNG output, renderer substitution, and error handling
for invalid output paths and renderers that fail to create a non-empty file.

## Design and refactoring

The generator is structured around the SOLID principles:

- **Single Responsibility:** QR rendering is separated from batch generation
  and output-directory validation.
- **Open/Closed:** New renderer implementations can be added through the
  `QrCodeRenderer` interface without changing the generation loop.
- **Liskov Substitution:** Renderer implementations are expected to return a
  safe file extension and create a non-empty file; the generator validates
  those expectations.
- **Interface Segregation:** The renderer interface contains only the two
  related operations required by the generator.
- **Dependency Inversion:** The generator accepts the renderer abstraction;
  the command-line entry point supplies the PNG implementation.

See [SOLID_REFACTOR.md](./SOLID_REFACTOR.md) for the detailed refactoring
rationale and test coverage.

