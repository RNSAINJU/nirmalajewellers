(function () {
  const html = document.getElementById('customerHtml');
  const themeIcon = document.getElementById('customerThemeIcon');
  const toast = document.getElementById('customerToast');
  let toastTimer = null;

  function initTheme() {
    if (!html) return;
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
      html.classList.remove('dark');
      if (themeIcon) themeIcon.textContent = 'light_mode';
    } else {
      html.classList.add('dark');
      if (themeIcon) themeIcon.textContent = 'dark_mode';
    }
  }

  window.toggleCustomerTheme = function () {
    if (!html) return;
    if (html.classList.contains('dark')) {
      html.classList.remove('dark');
      localStorage.setItem('theme', 'light');
      if (themeIcon) themeIcon.textContent = 'light_mode';
    } else {
      html.classList.add('dark');
      localStorage.setItem('theme', 'dark');
      if (themeIcon) themeIcon.textContent = 'dark_mode';
    }
  };

  window.showCustomerToast = function (message, type) {
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove('is-hidden', 'bg-red-600', 'bg-emerald-600', 'bg-background-dark');
    if (type === 'error') {
      toast.classList.add('bg-red-600');
    } else if (type === 'success') {
      toast.classList.add('bg-emerald-600');
    } else {
      toast.classList.add('bg-background-dark');
    }
    toast.classList.add('is-visible');
    toast.classList.remove('is-hidden');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
      toast.classList.remove('is-visible');
      toast.classList.add('is-hidden');
    }, 2800);
  };

  window.updateCustomerCartBadge = function () {
    const cart = JSON.parse(localStorage.getItem('cart') || '[]');
    const count = cart.reduce(function (sum, item) {
      return sum + (item.quantity || 1);
    }, 0);
    localStorage.setItem('cartCount', String(count));
    document.querySelectorAll('[data-cart-count]').forEach(function (el) {
      el.textContent = count;
      el.classList.toggle('hidden', count <= 0);
    });
    return count;
  };

  window.goToCustomerCart = function () {
    const cartUrl = document.body.dataset.cartUrl;
    if (cartUrl) window.location.href = cartUrl;
  };

  window.toggleCustomerMenu = function () {
    const sidebar = document.getElementById('customerSidebar');
    const overlay = document.getElementById('customerSidebarOverlay');
    if (!sidebar || !overlay) return;
    sidebar.classList.toggle('-translate-x-full');
    overlay.classList.toggle('hidden');
  };

  window.closeCustomerMenu = function () {
    const sidebar = document.getElementById('customerSidebar');
    const overlay = document.getElementById('customerSidebarOverlay');
    if (!sidebar || !overlay) return;
    sidebar.classList.add('-translate-x-full');
    overlay.classList.add('hidden');
  };

  window.toggleCustomerWishlist = function (event, productId, button) {
    if (event) {
      event.preventDefault();
      event.stopPropagation();
    }
    const key = 'wishlist';
    let wishlist = JSON.parse(localStorage.getItem(key) || '[]');
    const id = String(productId);
    const index = wishlist.indexOf(id);
    const icon = button ? button.querySelector('.material-icons-outlined') : null;

    if (index >= 0) {
      wishlist.splice(index, 1);
      if (icon) icon.textContent = 'favorite_border';
      if (button) button.classList.remove('text-primary');
      showCustomerToast('Removed from wishlist');
    } else {
      wishlist.push(id);
      if (icon) icon.textContent = 'favorite';
      if (button) button.classList.add('text-primary');
      showCustomerToast('Added to wishlist', 'success');
    }
    localStorage.setItem(key, JSON.stringify(wishlist));
    updateCustomerWishlistBadge();
  };

  window.updateCustomerWishlistBadge = function () {
    const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    document.querySelectorAll('[data-wishlist-count]').forEach(function (el) {
      el.textContent = wishlist.length;
      el.classList.toggle('hidden', wishlist.length <= 0);
    });
    return wishlist.length;
  };

  window.syncCustomerWishlistButtons = function () {
    const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    document.querySelectorAll('[data-wishlist-id]').forEach(function (button) {
      const id = button.getAttribute('data-wishlist-id');
      const icon = button.querySelector('.material-icons-outlined');
      if (wishlist.includes(String(id))) {
        if (icon) icon.textContent = 'favorite';
        button.classList.add('text-primary');
      }
    });
  };

  window.openCustomerWishlist = function () {
    const count = updateCustomerWishlistBadge();
    if (count === 0) {
      showCustomerToast('Your wishlist is empty');
      return;
    }
    showCustomerToast(count + ' item' + (count === 1 ? '' : 's') + ' saved in wishlist');
  };

  function initScrollChrome() {
    const bottomNav = document.getElementById('customerBottomNav');
    const topHeader = document.getElementById('customerHeader');
    if (!bottomNav && !topHeader) return;

    let lastScrollY = window.scrollY;
    window.addEventListener('scroll', function () {
      const currentScrollY = window.scrollY;
      if (currentScrollY <= 0) {
        bottomNav && bottomNav.classList.remove('translate-y-full');
        topHeader && topHeader.classList.remove('-translate-y-full');
        lastScrollY = currentScrollY;
        return;
      }
      if (Math.abs(currentScrollY - lastScrollY) < 8) return;
      if (currentScrollY > lastScrollY) {
        bottomNav && bottomNav.classList.add('translate-y-full');
        topHeader && topHeader.classList.add('-translate-y-full');
      } else {
        bottomNav && bottomNav.classList.remove('translate-y-full');
        topHeader && topHeader.classList.remove('-translate-y-full');
      }
      lastScrollY = currentScrollY;
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initTheme();
    updateCustomerCartBadge();
    updateCustomerWishlistBadge();
    syncCustomerWishlistButtons();
    initScrollChrome();

    if (toast) {
      toast.classList.add('is-hidden');
    }
  });
})();
