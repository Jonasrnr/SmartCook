import { initRecipeEdit } from "./edit_recipe.js";

const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebarTitle = document.getElementById('sidebar-title');
const navTexts = document.querySelectorAll('.nav-text');
const contentWrapper = document.getElementById('content-wrapper');

let isCollapsed = true;

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

document.addEventListener('DOMContentLoaded', function() {
    initRecipeEdit()
});

document.body.addEventListener('show-toast', function(evt) {
    const toast = document.getElementById('toast-notification');
    const messageEl = document.getElementById('toast-message');

    if (!evt.detail.message) {
        return;
    }

    const message = evt.detail.message;
    const type = evt.detail.type || 'info';

    messageEl.innerText = message;

    toast.classList.remove('bg-green-600', 'bg-red-600', 'bg-blue-600');

    if (type === 'success') {
        toast.classList.add('bg-green-600');
    } else if (type === 'error') {
        toast.classList.add('bg-red-600');
    } else {
        toast.classList.add('bg-blue-600');
    }

    toast.classList.remove('opacity-0');
    toast.classList.remove('pointer-events-none');
    toast.classList.remove('translate-x-full');

    setTimeout(() => {
        toast.classList.add('translate-x-full');
        toast.classList.add('opacity-0');
        setTimeout(() => {
            toast.classList.add('pointer-events-none');
        }, 500);
    }, 4000);
});

document.body.addEventListener('reload-content', function(evt) {
    //custom event "reload-content"
    setTimeout(() => {
        htmx.ajax('GET', window.location.href, { target: '#main-content', swap: 'innerHTML' });
    }, 200);
});