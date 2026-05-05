/**
 * Image Compressor for Ornament Photos
 * Compresses images before upload to reduce file size without quality loss
 */

class ImageCompressor {
    constructor(options = {}) {
        this.maxWidth = options.maxWidth || 1920;      // Max width in pixels
        this.maxHeight = options.maxHeight || 1920;     // Max height in pixels
        this.quality = options.quality || 0.85;         // JPEG quality (0.85 = 85%)
        this.maxFileSize = options.maxFileSize || 500;  // Target file size in KB
    }

    /**
     * Compress an image file
     * @param {File} file - The image file to compress
     * @param {Function} callback - Callback(compressedFile, originalSize, compressedSize)
     */
    compress(file, callback) {
        const reader = new FileReader();

        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const canvas = this._resizeImage(img);
                
                // Convert canvas to blob with quality
                canvas.toBlob((blob) => {
                    const compressedFile = new File(
                        [blob],
                        file.name,
                        { type: 'image/jpeg', lastModified: Date.now() }
                    );

                    callback(compressedFile, file.size, compressedFile.size);
                }, 'image/jpeg', this.quality);
            };
            img.src = e.target.result;
        };

        reader.readAsDataURL(file);
    }

    /**
     * Resize image to fit within max dimensions
     * @private
     */
    _resizeImage(img) {
        const canvas = document.createElement('canvas');
        let width = img.width;
        let height = img.height;

        // Calculate new dimensions maintaining aspect ratio
        if (width > height) {
            if (width > this.maxWidth) {
                height = Math.round((height * this.maxWidth) / width);
                width = this.maxWidth;
            }
        } else {
            if (height > this.maxHeight) {
                width = Math.round((width * this.maxHeight) / height);
                height = this.maxHeight;
            }
        }

        canvas.width = width;
        canvas.height = height;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0, width, height);

        return canvas;
    }

    /**
     * Format file size for display
     */
    static formatSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
}

// Initialize compressor on document ready
document.addEventListener('DOMContentLoaded', function() {
    const imageInputs = document.querySelectorAll('input[type="file"][accept*="image"]');
    const compressor = new ImageCompressor({
        quality: 0.85,      // 85% quality maintains near-perfect visual fidelity
        maxWidth: 1920,     // Resize to 1920px max (perfect for web)
        maxHeight: 1920
    });

    imageInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (!file) return;

            // Show processing indicator
            const originalSize = ImageCompressor.formatSize(file.size);
            const progressEl = document.createElement('div');
            progressEl.className = 'alert alert-info mt-2';
            progressEl.innerHTML = `<i class="bi bi-hourglass-split"></i> Compressing image...`;
            input.parentElement.insertAdjacentElement('afterend', progressEl);

            // Compress the image
            compressor.compress(file, (compressedFile, origSize, compSize) => {
                const compressedSize = ImageCompressor.formatSize(compSize);
                const savings = Math.round(((origSize - compSize) / origSize) * 100);

                // Replace file in input
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(compressedFile);
                input.files = dataTransfer.files;

                // Update progress message
                progressEl.className = 'alert alert-success mt-2';
                progressEl.innerHTML = `
                    <i class="bi bi-check-circle"></i> 
                    <strong>Image Optimized!</strong><br>
                    Original: ${originalSize} → Compressed: ${compressedSize} (${savings}% reduction)
                `;

                // Auto-hide after 5 seconds
                setTimeout(() => {
                    progressEl.style.display = 'none';
                }, 5000);
            });
        });
    });
});
