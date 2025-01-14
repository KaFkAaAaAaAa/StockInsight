document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('id_profile_picture');
    const clearButton = document.getElementById('clear_file');

    function updateClearButtonVisibility() {
        if (fileInput.value) {
            clearButton.style.display = 'inline-block';
        } else {
            clearButton.style.display = 'none';
        }
    }

    fileInput.addEventListener('change', updateClearButtonVisibility);

    clearButton.addEventListener('click', function () {
        fileInput.value = '';
        updateClearButtonVisibility();
    });

    updateClearButtonVisibility();
});