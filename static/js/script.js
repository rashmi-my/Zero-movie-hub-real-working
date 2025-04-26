document.addEventListener('DOMContentLoaded', function() {
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Preview image URL in admin panel
    const thumbnailUrlInput = document.getElementById('thumbnail_url');
    if (thumbnailUrlInput) {
        thumbnailUrlInput.addEventListener('blur', function() {
            const previewContainer = document.getElementById('thumbnail-preview');
            if (!previewContainer) {
                const container = document.createElement('div');
                container.id = 'thumbnail-preview';
                container.className = 'mt-2';
                
                if (this.value) {
                    const img = document.createElement('img');
                    img.src = this.value;
                    img.className = 'img-thumbnail';
                    img.style.maxHeight = '150px';
                    container.appendChild(img);
                }
                
                this.parentNode.appendChild(container);
            } else {
                if (this.value) {
                    previewContainer.innerHTML = `<img src="${this.value}" class="img-thumbnail" style="max-height: 150px;">`;
                } else {
                    previewContainer.innerHTML = '';
                }
            }
        });
    }
});
