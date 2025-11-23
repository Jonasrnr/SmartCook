document.addEventListener('DOMContentLoaded', function() {
    const pasteBtn = document.getElementById('paste-tiktok-btn');
    const inputField = document.getElementById('tiktok-link-input');
    if (pasteBtn && inputField) {
        pasteBtn.addEventListener('click', async() => {
            try {
                const text = await navigator.clipboard.readText();
                inputField.value = text;
            } catch (err) {
                console.error('Konnte Text nicht aus der Zwischenablage lesen: ', err);
            }
        });
    }
});