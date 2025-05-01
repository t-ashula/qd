/**
 * Main JavaScript file for QD application
 */

document.addEventListener('DOMContentLoaded', function () {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle audio player time updates for episode page
    const audioPlayer = document.getElementById('audio-player');
    if (audioPlayer) {
        const segments = document.querySelectorAll('.segment');

        // Update active segment based on current time
        audioPlayer.addEventListener('timeupdate', function () {
            const currentTime = audioPlayer.currentTime;

            segments.forEach(segment => {
                const playButton = segment.querySelector('.play-segment');
                if (!playButton) return;

                const start = parseFloat(playButton.getAttribute('data-start'));
                const end = parseFloat(playButton.getAttribute('data-end'));

                if (currentTime >= start && currentTime < end) {
                    segments.forEach(s => s.classList.remove('segment-active'));
                    segment.classList.add('segment-active');

                    // Scroll into view if not visible
                    const rect = segment.getBoundingClientRect();
                    const isVisible = (
                        rect.top >= 0 &&
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight)
                    );

                    if (!isVisible) {
                        segment.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            });
        });
    }

    // Search form validation
    const searchForm = document.querySelector('form[action="/search"]');
    if (searchForm) {
        searchForm.addEventListener('submit', function (event) {
            const searchInput = this.querySelector('input[name="q"]');
            if (!searchInput.value.trim()) {
                event.preventDefault();
                searchInput.classList.add('is-invalid');

                // Add validation message if not exists
                if (!this.querySelector('.invalid-feedback')) {
                    const feedback = document.createElement('div');
                    feedback.className = 'invalid-feedback';
                    feedback.textContent = 'Please enter a search query';
                    searchInput.parentNode.appendChild(feedback);
                }
            }
        });
    }
});