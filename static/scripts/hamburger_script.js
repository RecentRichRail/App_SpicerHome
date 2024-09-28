document.addEventListener('DOMContentLoaded', function () {
    const hamburgerMenu = document.getElementById('hamburger-menu');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('overlay');

    console.log('hamburgerMenu:', hamburgerMenu);
    console.log('sidebar:', sidebar);
    console.log('overlay:', overlay);

    // Toggle sidebar and overlay visibility
    function toggleSidebar() {
        console.log('Toggling sidebar');
        sidebar.classList.toggle('open');
        overlay.classList.toggle('show');
    }

    // Close sidebar and overlay when overlay is clicked
    overlay.addEventListener('click', function () {
        console.log('Overlay clicked');
        toggleSidebar();
    });

    // Open sidebar when hamburger menu is clicked
    hamburgerMenu.addEventListener('click', function () {
        console.log('Hamburger menu clicked');
        toggleSidebar();
    });

    // Update page title
    const pageTitleElement = document.getElementById('page-title');
    console.log('pageTitleElement:', pageTitleElement);
    if (pageTitleElement && pageTitleElement.dataset.title) {
        document.title = pageTitleElement.dataset.title;
        console.log('Document title set to:', document.title);
    }

    // Render sidebar links dynamically if they are provided
    const sidebarLinksElement = document.getElementById('sidebar-links');
    console.log('sidebarLinksElement:', sidebarLinksElement);
    if (sidebarLinksElement && sidebarLinksElement.dataset.links) {
        const links = JSON.parse(sidebarLinksElement.dataset.links);
        console.log('Parsed links:', links);
        sidebarLinksElement.innerHTML = links.map(link => 
            `<li><a href="${link.href}" class="tab-link" data-tab="${link.data_tab}">${link.text}</a></li>`
        ).join('');
    }
});
