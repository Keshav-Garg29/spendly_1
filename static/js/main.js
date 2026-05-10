// main.js — students will add JavaScript here as features are built

// Video Modal functionality
(function() {
    const modal = document.getElementById('videoModal');
    const openBtn = document.getElementById('openModalBtn');
    const closeBtn = document.getElementById('closeModalBtn');
    const videoFrame = document.getElementById('videoFrame');

    // YouTube video URL (placeholder - replace with actual video ID)
    const videoUrl = 'https://www.youtube.com/embed/dQw4w9WgXcQ?autoplay=1';

    if (openBtn && modal && videoFrame) {
        // Open modal
        openBtn.addEventListener('click', function() {
            modal.classList.add('active');
            videoFrame.src = videoUrl;
        });

        // Close modal function
        function closeModal() {
            modal.classList.remove('active');
            videoFrame.src = ''; // Stop video by clearing src
        }

        // Close on close button click
        if (closeBtn) {
            closeBtn.addEventListener('click', closeModal);
        }

        // Close on overlay click (outside modal)
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });

        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modal.classList.contains('active')) {
                closeModal();
            }
        });
    }
})();
