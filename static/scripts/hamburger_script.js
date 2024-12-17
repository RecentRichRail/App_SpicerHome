document.addEventListener('DOMContentLoaded', function () {
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    // Toggle sidebar and overlay visibility
    function toggleSidebar() {
        sidebar.classList.toggle('translate-x-0');
        sidebar.classList.toggle('-translate-x-full');
        overlay.classList.toggle('hidden');
    }

    // Close sidebar and overlay when overlay is clicked
    overlay.addEventListener('click', function () {
        toggleSidebar();
    });

    // Open sidebar when hamburger menu is clicked
    hamburgerMenu.addEventListener('click', function () {
        toggleSidebar();
    });

    // Update page title
    const pageTitleElement = document.getElementById('page-title');
    if (pageTitleElement && pageTitleElement.dataset.title) {
        document.title = pageTitleElement.dataset.title;
    }

    // Render sidebar links dynamically if they are provided
    const sidebarLinksElement = document.getElementById('sidebar-links');
    if (sidebarLinksElement && sidebarLinksElement.dataset.links) {
        const links = JSON.parse(sidebarLinksElement.dataset.links);
        sidebarLinksElement.innerHTML = links.map(link => 
            `<li class="p-2"><a href="${link.href}" class="text-white no-underline" data-tab="${link.data_tab}">${link.text}</a></li>`
        ).join('');
    }
});