<?php

declare(strict_types=1);

require __DIR__ . '/../generate_qrcodes.php';

function assertTest(bool $condition, string $message): void
{
    if (!$condition) {
        throw new RuntimeException($message);
    }
}

$testRoot = sys_get_temp_dir() . '/qrcode-wizard-test-' . bin2hex(random_bytes(8));
$outputDir = $testRoot . '/generated';
$blockedPath = $testRoot . '/not-a-directory';

mkdir($testRoot, 0777, true);
file_put_contents($blockedPath, 'file');

try {
    generateQrCodes($outputDir, new PngQrCodeRenderer(), 2);

    foreach (['00001', '00002'] as $number) {
        $filePath = "{$outputDir}/qr_{$number}.png";
        assertTest(is_file($filePath), "Expected generated QR code: {$filePath}");
        assertTest(
            file_get_contents($filePath, false, null, 0, 8) === "\x89PNG\r\n\x1a\n",
            "Expected a valid PNG signature: {$filePath}"
        );
    }

    $customRenderer = new class implements QrCodeRenderer {
        public function fileExtension(): string
        {
            return 'test';
        }

        public function render(string $number, string $filePath): void
        {
            file_put_contents($filePath, $number);
        }
    };
    $customOutputDir = $testRoot . '/custom';
    generateQrCodes($customOutputDir, $customRenderer, 1);
    assertTest(
        file_get_contents("{$customOutputDir}/qr_00001.test") === '00001',
        'Expected the injected renderer to control output generation and extension.'
    );

    $incompleteRenderer = new class implements QrCodeRenderer {
        public function fileExtension(): string
        {
            return 'test';
        }

        public function render(string $number, string $filePath): void
        {
        }
    };
    try {
        generateQrCodes("{$testRoot}/incomplete", $incompleteRenderer, 1);
        throw new RuntimeException('Expected an incomplete renderer to fail.');
    } catch (RuntimeException $exception) {
        assertTest(
            str_contains($exception->getMessage(), 'did not create a non-empty file'),
            'Expected an explicit error when a renderer fails its output contract.'
        );
    }

    try {
        ensureOutputDirectory($blockedPath);
        throw new RuntimeException('Expected a non-directory output path to fail.');
    } catch (RuntimeException $exception) {
        assertTest(
            str_contains($exception->getMessage(), 'Output path is not a directory'),
            'Expected an explicit error for a non-directory output path.'
        );
    }

    echo "All QR code generation tests passed.\n";
} finally {
    foreach (glob("{$outputDir}/*") ?: [] as $filePath) {
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
        rmdir("{$testRoot}/incomplete");
    }

    unlink($blockedPath);
    rmdir($testRoot);
}
