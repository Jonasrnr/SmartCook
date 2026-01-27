function initTikTokPaste() {
    // TODO: Paste seems buggy sometimes
    const pasteBtn = document.getElementById('paste-tiktok-btn');
    const inputField = document.getElementById('tiktok-link-input');
    const form = document.getElementById('tiktok-form');
    if (!pasteBtn || !inputField || !form) return;

    pasteBtn.addEventListener('click', async() => {
        try {
            const text = await navigator.clipboard.readText();
            inputField.value = text;

            htmx.trigger(form, 'submit');
        } catch (err) {
            console.error('Paste load error', err);
        }
    });
}

function initRecipeScroller(container = document) {
    const scroller = container.querySelector("#recipe-scroller");
    if (!scroller) return;

    const inner = scroller.querySelector("div");
    if (!inner || inner.scrollWidth <= scroller.clientWidth) return;

    let speed = 0.5;
    let isPaused = false;
    let direction = 1;
    let pauseFrame = 0;
    const pauseDuration = 60

    // pause on hover/touch
    scroller.addEventListener("mouseenter", () => isPaused = true);
    scroller.addEventListener("mouseleave", () => isPaused = false);
    scroller.addEventListener("touchstart", () => isPaused = true);
    scroller.addEventListener("touchend", () => isPaused = false);

    function autoScroll() {
        if (!isPaused) {
            let next = scroller.scrollLeft + speed * direction;

            // change direction at edges
            if (next >= scroller.scrollWidth - scroller.clientWidth) {
                if (pauseFrame < pauseDuration) {
                    pauseFrame++;
                    next = scroller.scrollWidth - scroller.clientWidth; // genau am rechten Rand
                } else {
                    direction = -1;
                    pauseFrame = 0;
                    next = scroller.scrollWidth - scroller.clientWidth;
                }
            }

            if (next <= 0) {
                if (pauseFrame < pauseDuration) {
                    pauseFrame++;
                    next = 0;
                } else {
                    direction = 1;
                    pauseFrame = 0;
                    next = 0;
                }
            }

            scroller.scrollLeft = next;
        }

        requestAnimationFrame(autoScroll);
    }
    autoScroll();
}

//Init on Page Load
document.addEventListener("DOMContentLoaded", () => {
    initTikTokPaste();
    initRecipeScroller();
});

// Init on HTMX Swap
document.body.addEventListener("htmx:afterSwap", (evt) => {
    if (evt.detail.target.querySelector("#recipe-scroller")) {
        initRecipeScroller(evt.detail.target);
    }
});