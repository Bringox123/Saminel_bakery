/**
 * Saminel Bakery — Offline-First IndexedDB Cart & POS Synchronization Engine
 * Provides resilient client-side state persistence for cart items, product catalog
 * caching, and an offline order queue that syncs automatically when connectivity returns.
 */
(function (window) {
  'use strict';

  var DB_NAME = 'saminel_pos_db';
  var DB_VERSION = 1;
  var CART_STORAGE_KEY = 'saminel_cart_v1';

  function openDatabase() {
    return new Promise(function (resolve, reject) {
      if (!window.indexedDB) {
        resolve(null);
        return;
      }
      var request = window.indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = function (event) {
        var db = event.target.result;
        if (!db.objectStoreNames.contains('cart_items')) {
          db.createObjectStore('cart_items', { keyPath: 'productId' });
        }
        if (!db.objectStoreNames.contains('offline_orders')) {
          db.createObjectStore('offline_orders', { keyPath: 'clientOrderId' });
        }
        if (!db.objectStoreNames.contains('catalog_cache')) {
          db.createObjectStore('catalog_cache', { keyPath: 'id' });
        }
      };
      request.onsuccess = function (event) {
        resolve(event.target.result);
      };
      request.onerror = function () {
        resolve(null);
      };
    });
  }

  function getLocalCart() {
    try {
      var raw = window.localStorage.getItem(CART_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (e) {
      return [];
    }
  }

  function saveLocalCart(items) {
    try {
      window.localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    } catch (e) {}
    openDatabase().then(function (db) {
      if (!db) return;
      var tx = db.transaction('cart_items', 'readwrite');
      var store = tx.objectStore('cart_items');
      store.clear();
      items.forEach(function (item) {
        store.put(item);
      });
    });
    updateCartBadges(items);
  }

  function updateCartBadges(items) {
    var cart = items || getLocalCart();
    var totalCount = cart.reduce(function (sum, item) {
      return sum + (parseInt(item.quantity, 10) || 0);
    }, 0);
    var badges = document.querySelectorAll('.cart-badge');
    badges.forEach(function (badge) {
      badge.textContent = String(totalCount);
    });
  }

  function addToCart(product) {
    var cart = getLocalCart();
    var existing = cart.find(function (item) {
      return String(item.productId) === String(product.productId);
    });
    if (existing) {
      existing.quantity += product.quantity || 1;
    } else {
      cart.push({
        productId: String(product.productId),
        name: product.name,
        price: parseFloat(product.price) || 0,
        category: product.category || 'Bakery',
        quantity: product.quantity || 1
      });
    }
    saveLocalCart(cart);
    return cart;
  }

  function updateQuantity(productId, delta) {
    var cart = getLocalCart();
    cart = cart.map(function (item) {
      if (String(item.productId) === String(productId)) {
        item.quantity = Math.max(0, (parseInt(item.quantity, 10) || 0) + delta);
      }
      return item;
    }).filter(function (item) {
      return item.quantity > 0;
    });
    saveLocalCart(cart);
    return cart;
  }

  function clearCart() {
    saveLocalCart([]);
  }

  function queueOfflineOrder(orderPayload) {
    var record = {
      clientOrderId: 'LOCAL-' + Date.now() + '-' + Math.random().toString(36).substring(2, 7).toUpperCase(),
      items: orderPayload.items || [],
      totalAmount: orderPayload.totalAmount || 0,
      notes: orderPayload.notes || '',
      createdAt: new Date().toISOString(),
      synced: false
    };
    return openDatabase().then(function (db) {
      if (!db) {
        var fallbackQueue = JSON.parse(window.localStorage.getItem('saminel_offline_orders') || '[]');
        fallbackQueue.push(record);
        window.localStorage.setItem('saminel_offline_orders', JSON.stringify(fallbackQueue));
        return record;
      }
      return new Promise(function (resolve) {
        var tx = db.transaction('offline_orders', 'readwrite');
        tx.objectStore('offline_orders').put(record);
        tx.oncomplete = function () {
          resolve(record);
        };
        tx.onerror = function () {
          resolve(record);
        };
      });
    });
  }

  function getQueuedOrders() {
    return openDatabase().then(function (db) {
      if (!db) {
        return JSON.parse(window.localStorage.getItem('saminel_offline_orders') || '[]');
      }
      return new Promise(function (resolve) {
        var tx = db.transaction('offline_orders', 'readonly');
        var req = tx.objectStore('offline_orders').getAll();
        req.onsuccess = function () {
          resolve(req.result || []);
        };
        req.onerror = function () {
          resolve([]);
        };
      });
    });
  }

  function removeQueuedOrder(clientOrderId) {
    return openDatabase().then(function (db) {
      if (!db) {
        var queue = JSON.parse(window.localStorage.getItem('saminel_offline_orders') || '[]');
        window.localStorage.setItem(
          'saminel_offline_orders',
          JSON.stringify(queue.filter(function (o) { return o.clientOrderId !== clientOrderId; }))
        );
        return;
      }
      return new Promise(function (resolve) {
        var tx = db.transaction('offline_orders', 'readwrite');
        tx.objectStore('offline_orders').delete(clientOrderId);
        tx.oncomplete = function () { resolve(); };
        tx.onerror = function () { resolve(); };
      });
    });
  }

  function getCsrfToken() {
    var match = document.cookie.match(/csrftoken=([^;]+)/);
    if (match) return match[1];
    var input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  }

  function syncQueuedOrders() {
    if (!navigator.onLine) {
      return Promise.resolve({ synced: 0, pending: 0 });
    }
    return getQueuedOrders().then(function (orders) {
      if (!orders.length) {
        return { synced: 0, pending: 0 };
      }
      return fetch('/api/orders/sync/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify({ orders: orders })
      })
      .then(function (res) {
        if (!res.ok) throw new Error('Sync failed');
        return res.json();
      })
      .then(function (data) {
        var syncedIds = data.synced_client_ids || [];
        return Promise.all(syncedIds.map(removeQueuedOrder)).then(function () {
          return { synced: syncedIds.length, orders: data.orders || [] };
        });
      })
      .catch(function () {
        return { synced: 0, pending: orders.length };
      });
    });
  }

  window.addEventListener('online', function () {
    syncQueuedOrders().then(function (res) {
      if (res.synced > 0) {
        window.dispatchEvent(new CustomEvent('saminel:orders-synced', { detail: res }));
      }
    });
  });

  document.addEventListener('DOMContentLoaded', function () {
    updateCartBadges();
    document.body.addEventListener('click', function (event) {
      var btn = event.target.closest('[data-add-to-cart]');
      if (!btn) return;
      event.preventDefault();
      addToCart({
        productId: btn.getAttribute('data-product-id'),
        name: btn.getAttribute('data-product-name'),
        price: btn.getAttribute('data-product-price'),
        category: btn.getAttribute('data-product-category') || 'Bakery',
        quantity: 1
      });
      var originalText = btn.textContent;
      btn.textContent = 'Added ✓';
      setTimeout(function () {
        btn.textContent = originalText;
      }, 900);
    });
  });

  window.SaminelOfflinePOS = {
    getCart: getLocalCart,
    addToCart: addToCart,
    updateQuantity: updateQuantity,
    clearCart: clearCart,
    queueOfflineOrder: queueOfflineOrder,
    getQueuedOrders: getQueuedOrders,
    syncQueuedOrders: syncQueuedOrders
  };
})(window);
