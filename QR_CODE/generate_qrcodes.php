<?php

declare(strict_types=1);

require __DIR__ . '/vendor/autoload.php';

use Endroid\QrCode\Builder\Builder;
use Endroid\QrCode\Encoding\Encoding;
use Endroid\QrCode\ErrorCorrectionLevel;
use Endroid\QrCode\Label\LabelAlignment;
use Endroid\QrCode\Label\Font\OpenSans;
use Endroid\QrCode\RoundBlockSizeMode;
use Endroid\QrCode\Writer\PngWriter;

interface QrCodeRenderer
{
    /** Returns the filename extension without a leading dot. */
    public function fileExtension(): string;

    /** Writes a non-empty QR code file to the requested path. */
    public function render(string $number, string $filePath): void;
}

final class PngQrCodeRenderer implements QrCodeRenderer
{
    public function fileExtension(): string
    {
        return 'png';
    }

    public function render(string $number, string $filePath): void
    {
        $builder = new Builder(
            writer: new PngWriter(),
            writerOptions: [],
            validateResult: false,
            data: $number,
            encoding: new Encoding('UTF-8'),
            errorCorrectionLevel: ErrorCorrectionLevel::High,
            size: 300,
            margin: 10,
            roundBlockSizeMode: RoundBlockSizeMode::Margin,
            labelText: $number,
            labelFont: new OpenSans(16),
            labelAlignment: LabelAlignment::Center
        );

        $builder->build()->saveToFile($filePath);
    }
}

function ensureOutputDirectory(string $outputDir): void
{
    if (file_exists($outputDir) && !is_dir($outputDir)) {
        throw new RuntimeException("Output path is not a directory: {$outputDir}");
    }

    if (!is_dir($outputDir) && !mkdir($outputDir, 0777, true) && !is_dir($outputDir)) {
        throw new RuntimeException("Unable to create output directory: {$outputDir}");
    }

    if (!is_writable($outputDir)) {
        throw new RuntimeException("Output directory is not writable: {$outputDir}");
    }
}

function generateQrCodes(string $outputDir, QrCodeRenderer $renderer, int $count = 10000): void
{
    if ($count < 1) {
        throw new InvalidArgumentException('The QR code count must be at least 1.');
    }

    ensureOutputDirectory($outputDir);
    $extension = $renderer->fileExtension();
    if (!preg_match('/\A[a-z0-9]+\z/i', $extension)) {
        throw new RuntimeException("Renderer returned an invalid file extension: {$extension}");
    }

    for ($i = 1; $i <= $count; $i++) {
        $number = str_pad((string) $i, 5, '0', STR_PAD_LEFT);
        $filePath = "{$outputDir}/qr_{$number}.{$extension}";
        $renderer->render($number, $filePath);

        $fileSize = is_file($filePath) ? filesize($filePath) : false;
        if ($fileSize === false || $fileSize === 0) {
            throw new RuntimeException("Renderer did not create a non-empty file: {$filePath}");
        }
    }
}

$outputDir = __DIR__ . '/qrcodes';
if (PHP_SAPI === 'cli' && realpath($_SERVER['SCRIPT_FILENAME']) === __FILE__) {
    generateQrCodes($outputDir, new PngQrCodeRenderer());
    echo "✅ Done! Generated 10,000 QR codes in: {$outputDir}\n";
}
