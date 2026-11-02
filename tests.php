<?php

declare(strict_types=1);

require_once __DIR__ . "/../generate_qrcodes.php";

const FIRST_QR_NUMBER = "00001";
const EXISTING_OUTPUT_CONTENTS = "previous output";

final class TestAssertionFailed extends LogicException
{
}

final class RendererTestFailure extends RuntimeException
{
}

function assertTest(bool $condition, string $message): void
{
    if (!$condition) {
        throw new TestAssertionFailed($message);
    }
}

$testRoot =
    sys_get_temp_dir() . "/qrcode-wizard-test-" . bin2hex(random_bytes(8));
$outputDir = $testRoot . "/generated";
$blockedPath = $testRoot . "/not-a-directory";

mkdir($testRoot, 0777, true);
file_put_contents($blockedPath, "file");

try {
    generateQrCodes($outputDir, new PngQrCodeRenderer(), 2);

    foreach ([FIRST_QR_NUMBER, "00002"] as $number) {
        $filePath = "{$outputDir}/qr_{$number}.png";
        assertTest(
            is_file($filePath),
            "Expected generated QR code: {$filePath}",
        );
        assertTest(
            file_get_contents($filePath, false, null, 0, 8) ===
                "\x89PNG\r\n\x1a\n",
            "Expected a valid PNG signature: {$filePath}",
        );
    }

    $customRenderer = new class implements QrCodeRenderer {
        public function fileExtension(): string
        {
            return "test";
        }

        public function render(string $number, string $filePath): void
        {
            file_put_contents($filePath, $number);
        }
    };
    $customOutputDir = $testRoot . "/custom";
    generateQrCodes($customOutputDir, $customRenderer, 1);
    assertTest(
        file_get_contents("{$customOutputDir}/qr_00001.test") === "00001",
        "Expected the injected renderer to control output generation and extension.",
    );

    $incompleteRenderer = new class implements QrCodeRenderer {
        public function fileExtension(): string
        {
            return "test";
        }

        public function render(string $number, string $filePath): void
        {
            // Deliberately omit output to verify renderer contract enforcement.
        }
    };
    $incompleteOutputDir = "{$testRoot}/incomplete";
    mkdir($incompleteOutputDir);
    file_put_contents(
        "{$incompleteOutputDir}/qr_00001.test",
        EXISTING_OUTPUT_CONTENTS,
    );
    $incompleteRendererFailed = false;
    try {
        generateQrCodes($incompleteOutputDir, $incompleteRenderer, 1);
    } catch (QrCodeRendererContractException $exception) {
        $incompleteRendererFailed = true;
        assertTest(
            str_contains(
                $exception->getMessage(),
                "did not create a non-empty file",
            ),
            "Expected an explicit error when a renderer fails its output contract.",
        );
    }
    assertTest(
        $incompleteRendererFailed,
        "Expected an incomplete renderer to fail.",
    );
    assertTest(
        file_get_contents("{$incompleteOutputDir}/qr_00001.test") ===
            EXISTING_OUTPUT_CONTENTS,
        "Expected failed rendering to preserve the existing output file.",
    );

    $throwingRenderer = new class implements QrCodeRenderer {
        public function fileExtension(): string
        {
            return "test";
        }

        public function render(string $number, string $filePath): void
        {
            file_put_contents($filePath, "partial output");
            throw new RendererTestFailure("Renderer failed.");
        }
    };
    $rendererExceptionPropagated = false;
    try {
        generateQrCodes($incompleteOutputDir, $throwingRenderer, 1);
    } catch (RendererTestFailure $exception) {
        $rendererExceptionPropagated = true;
        assertTest(
            $exception->getMessage() === "Renderer failed.",
            "Expected the original renderer exception to propagate.",
        );
    }
    assertTest(
        $rendererExceptionPropagated,
        "Expected a renderer exception to propagate.",
    );
    assertTest(
        file_get_contents("{$incompleteOutputDir}/qr_00001.test") ===
            EXISTING_OUTPUT_CONTENTS,
        "Expected renderer exceptions to preserve the existing output file.",
    );
    assertTest(
        glob("{$incompleteOutputDir}/.qr_*") === [],
        "Expected failed renders to clean up temporary files.",
    );

    generateQrCodes($incompleteOutputDir, $customRenderer, 1);
    assertTest(
        file_get_contents("{$incompleteOutputDir}/qr_00001.test") ===
            FIRST_QR_NUMBER,
        "Expected successful rendering to replace the previous output.",
    );

    $directoryFailureReported = false;
    try {
        ensureOutputDirectory($blockedPath);
    } catch (OutputDirectoryException $exception) {
        $directoryFailureReported = true;
        assertTest(
            str_contains(
                $exception->getMessage(),
                "Output path is not a directory",
            ),
            "Expected an explicit error for a non-directory output path.",
        );
    }
    assertTest(
        $directoryFailureReported,
        "Expected a non-directory output path to fail.",
    );

    echo "All QR code generation tests passed.\n";
} finally {
    foreach (glob("{$outputDir}/*") ?: [] as $filePath) {
        unlink($filePath);
    }
    foreach (glob("{$outputDir}/.qr_*") ?: [] as $filePath) {
        unlink($filePath);
    }
    if (is_dir($outputDir)) {
        rmdir($outputDir);
    }

    foreach (glob("{$testRoot}/custom/*") ?: [] as $filePath) {
        unlink($filePath);
    }

    if (is_dir("{$testRoot}/custom")) {
        rmdir("{$testRoot}/custom");
    }

    if (is_dir("{$testRoot}/incomplete")) {
        foreach (glob("{$testRoot}/incomplete/.qr_*") ?: [] as $filePath) {
            unlink($filePath);
        }

        foreach (glob("{$testRoot}/incomplete/*") ?: [] as $filePath) {
            unlink($filePath);
        }

        rmdir("{$testRoot}/incomplete");
    }

    unlink($blockedPath);
    rmdir($testRoot);
}
