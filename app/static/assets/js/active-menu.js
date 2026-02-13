document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname.replace(/\/$/, "");

  const subMenuItems = document.querySelectorAll(".sub-menu-item");

  subMenuItems.forEach((item) => {
    if (!item.href) return;

    const itemPath = new URL(item.href, window.location.origin).pathname.replace(/\/$/, "");

    if (itemPath === currentPath) {
      item.classList.add("active");

      // subir a parent-menu-item
      let parentMenu = item.closest(".parent-menu-item");
      while (parentMenu && !parentMenu.classList.contains("processed")) {
        const parentLink = parentMenu.querySelector("a");
        if (parentLink) parentLink.classList.add("active");
        parentMenu.classList.add("processed");
        parentMenu = parentMenu.closest(".parent-parent-menu-item");
      }

      // top-level
      const topLevelMenu = item.closest(".parent-parent-menu-item");
      if (topLevelMenu) {
        const topLevelLink = topLevelMenu.querySelector(".home-link");
        if (topLevelLink) topLevelLink.classList.add("active");
      }
    }
  });
});
