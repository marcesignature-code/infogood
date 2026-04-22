(function () {
  function updateBookmarkButton(button, saved) {
    const icon = button.querySelector("i");
    button.dataset.saved = saved ? "true" : "false";
    button.classList.toggle("is-saved", saved);
    button.setAttribute("data-bs-title", saved ? "Remove Bookmark" : "Save Listing");
    button.setAttribute("aria-pressed", saved ? "true" : "false");

    if (icon) {
      icon.classList.remove("bi-suit-heart", "bi-suit-heart-fill");
      icon.classList.add(saved ? "bi-suit-heart-fill" : "bi-suit-heart");
    }

    if (button.getAttribute("title")) {
      button.setAttribute("title", saved ? "Remove Bookmark" : "Save Listing");
    }
  }

  function syncButtonsForListing(listingId, saved) {
    const selector = '[data-bookmark-toggle][data-listing-id="' + listingId + '"]';
    document.querySelectorAll(selector).forEach(function (button) {
      updateBookmarkButton(button, saved);
    });
  }

  async function toggleBookmark(button) {
    const listingId = (button.dataset.listingId || "").trim();
    if (!listingId) {
      return;
    }

    button.classList.add("disabled");

    try {
      const response = await fetch("/bookmark/toggle/" + listingId, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "X-Requested-With": "XMLHttpRequest",
        },
      });

      const payload = await response.json().catch(function () {
        return {};
      });

      if (!response.ok || payload.ok === false) {
        throw new Error(payload.error || "Bookmark update failed");
      }

      syncButtonsForListing(listingId, Boolean(payload.saved));
    } catch (error) {
      console.error("Bookmark toggle error:", error);
    } finally {
      button.classList.remove("disabled");
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-bookmark-toggle]").forEach(function (button) {
      const saved = button.dataset.saved === "true";
      updateBookmarkButton(button, saved);
    });
  });

  document.addEventListener("click", function (event) {
    const button = event.target.closest("[data-bookmark-toggle]");
    if (!button) {
      return;
    }

    event.preventDefault();
    toggleBookmark(button);
  });
})();
