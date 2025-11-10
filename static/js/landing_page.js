document.addEventListener('DOMContentLoaded', function() {
    const pasteBtn = document.getElementById('paste-tiktok-btn');
    const inputField = document.getElementById('tiktok-link-input');

    pasteBtn.addEventListener('click', async() => {
        try {
            const text = await navigator.clipboard.readText();
            inputField.value = text;
        } catch (err) {
            console.error('Konnte Text nicht aus der Zwischenablage lesen: ', err);
            alert('Fehler beim Einfügen des Links. Bitte manuell einfügen.');
        }
    });
    pasteBtn.addEventListener('click', async() => {
        try {
            const text = await navigator.clipboard.readText();
            inputField.value = text;
            document.getElementById('tiktok-form').submit();
        } catch (err) {
            console.error(err);
            alert('Fehler beim Einfügen des Links.');
        }
    });
});