<?php

declare(strict_types=1);

namespace QRCodeWizard\SonarLintReview;

require_once __DIR__ . "/vendor/autoload.php";

use Endroid\QrCode\Builder\Builder;
use Endroid\QrCode\Encoding\Encoding;
use Endroid\QrCode\ErrorCorrectionLevel;
use Endroid\QrCode\Label\LabelAlignment;
use Endroid\QrCode\Label\Font\OpenSans;
use Endroid\QrCode\RoundBlockSizeMode;
use Endroid\QrCode\Writer\PngWriter;

class QrCodeGenerationException extends \RuntimeException
{
}

final class OutputDirectoryException extends QrCodeGenerationException
{
}

final class QrCodeRendererContractException extends QrCodeGenerationException
{
}

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
        return "png";
    }

    public function render(string $number, string $filePath): void
    {
        $builder = new Builder(
            writer: new PngWriter(),
            writerOptions: [],
            validateResult: false,
            data: $number,
            encoding: new Encoding("UTF-8"),
            errorCorrectionLevel: ErrorCorrectionLevel::High,
            size: 300,
            margin: 10,
            roundBlockSizeMode: RoundBlockSizeMode::Margin,
            labelText: $number,
            labelFont: new OpenSans(16),
            labelAlignment: LabelAlignment::Center,
        );

        $builder->build()->saveToFile($filePath);
    }
}

function ensureOutputDirectory(string $outputDir): void
{
    if (file_exists($outputDir) && !is_dir($outputDir)) {
        throw new OutputDirectoryException(
            "Output path is not a directory: {$outputDir}",
        );
    }

    if (
        !is_dir($outputDir) &&
        !mkdir($outputDir, 0755, true) &&
        !is_dir($outputDir)
    ) {
        throw new OutputDirectoryException(
            "Unable to create output directory: {$outputDir}",
        );
    }

    if (!is_writable($outputDir)) {
        throw new OutputDirectoryException(
            "Output directory is not writable: {$outputDir}",
        );
    }
}

function removeTemporaryQrCode(string $temporaryPath, \Throwable $cause): void
{
    if (
        (!file_exists($temporaryPath) && !is_link($temporaryPath)) ||
        unlink($temporaryPath)
    ) {
        return;
    }

    throw new QrCodeGenerationException(
        "Unable to clean up temporary QR code file: {$temporaryPath}",
        0,
        $cause,
    );
}

function renderQrCodeFile(
    QrCodeRenderer $renderer,
    string $number,
    string $filePath,
    string $extension,
): void {
    $fileName = basename($filePath, ".{$extension}");
    $temporaryPath =
        dirname($filePath) .
        "/.{$fileName}." .
        bin2hex(random_bytes(8)) .
        ".{$extension}";

    try {
        $renderer->render($number, $temporaryPath);

        $fileSize = is_file($temporaryPath) ? filesize($temporaryPath) : false;
        if ($fileSize === false || $fileSize === 0) {
            throw new QrCodeRendererContractException(
                "Renderer did not create a non-empty file: {$filePath}",
            );
        }

        if (!rename($temporaryPath, $filePath)) {
            throw new QrCodeGenerationException(
                "Unable to move generated QR code into place: {$filePath}",
            );
        }
    } catch (\Throwable $exception) {
        removeTemporaryQrCode($temporaryPath, $exception);
        throw $exception;
    }
}

function generateQrCodes(
    string $outputDir,
    QrCodeRenderer $renderer,
    int $count = 10000,
): void {
    if ($count < 1) {
        throw new QrCodeGenerationException(
            "The QR code count must be at least 1.",
        );
    }

    ensureOutputDirectory($outputDir);
    $extension = $renderer->fileExtension();
    if (!preg_match("/\A[a-z0-9]+\z/i", $extension)) {
        throw new QrCodeRendererContractException(
            "Renderer returned an invalid file extension: {$extension}",
        );
    }

    for ($i = 1; $i <= $count; $i++) {
        $number = str_pad((string) $i, 5, "0", STR_PAD_LEFT);
        $filePath = "{$outputDir}/qr_{$number}.{$extension}";
        renderQrCodeFile($renderer, $number, $filePath, $extension);
    }
}
