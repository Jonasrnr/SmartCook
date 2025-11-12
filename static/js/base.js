const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebarTitle = document.getElementById('sidebar-title');
const navTexts = document.querySelectorAll('.nav-text');
const contentWrapper = document.getElementById('content-wrapper');

let isCollapsed = true;

navTexts.forEach(text => {
    text.classList.add('hidden');
});

sidebarToggle.addEventListener('click', () => {
    isCollapsed = !isCollapsed;
    if (isCollapsed) {
        sidebar.classList.remove('w-56');
        sidebar.classList.add('w-20');

        contentWrapper.classList.remove('ml-56');
        contentWrapper.classList.add('ml-20');

        navTexts.forEach(text => {
            text.classList.add('hidden');
            text.classList.remove('opacity-100');
        });

        setTimeout(() => {
            sidebarTitle.classList.add('hidden');
        }, 100);

        sidebarToggle.style.transform = 'rotate(180deg)';
    } else {
        sidebar.classList.remove('w-20');
        sidebar.classList.add('w-56');

        contentWrapper.classList.remove('ml-20');
        contentWrapper.classList.add('ml-56');

        sidebarTitle.classList.remove('hidden');

        navTexts.forEach(text => {
            text.classList.remove('hidden');
            setTimeout(() => {
                text.classList.add('opacity-100');
            }, 50);
        });

        sidebarToggle.style.transform = 'rotate(0deg)';
    }
});

const overlay = document.getElementById('loading-overlay');
const content = document.getElementById('content-wrapper');

window.domReadyQueue = [];
window.onDomReady = function(callback) {
    if (document.readyState === "loading") {
        window.domReadyQueue.push(callback);
    } else {
        callback();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const tiktokForm = document.getElementById('tiktok-form');
    const tiktokInput = document.getElementById('tiktok-link-input');

    if (tiktokForm) {
        tiktokForm.addEventListener('submit', function() {
            overlay.style.display = 'flex';
            overlay.classList.remove('opacity-0');
            overlay.querySelector('span').textContent = 'Rezept wird verarbeitet...';
        });
    }

    if (tiktokInput && tiktokForm) {
        tiktokInput.addEventListener('paste', function() {
            setTimeout(() => {
                tiktokForm.submit();
            }, 100);
        });
    }
    window.domReadyQueue.forEach(fn => fn());
});

window.addEventListener('load', () => {
    overlay.classList.add('opacity-0');
    setTimeout(() => {
        overlay.style.display = 'none';
    }, 500);
    content.classList.remove('opacity-0');
});

function handleImageError(imageElement, recipeId) {
    // ChatGPT
    imageElement.onerror = () => {}; // Verhindert Endlosschleifen und Konsolenfehler

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        console.error("CSRF token not found.");
        return;
    }

    fetch(`/recipe/refresh_thumbnail/${recipeId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok' && data.thumbnail_url) {
                imageElement.src = data.thumbnail_url;
            }
        })
        .catch(error => console.error('Error refreshing thumbnail:', error));
}