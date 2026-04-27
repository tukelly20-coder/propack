/**
 * Safe localStorage Polyfill - Wraps localStorage với try-catch
 * Ngăn Tracking Prevention errors làm crash app
 */
(function() {
    'use strict';

    // Wrap initial access in try-catch to handle cases where localStorage throws
    let originalLocalStorage;
    try {
        originalLocalStorage = window.localStorage;
    } catch (e) {
        console.warn('[Storage] localStorage access failed, using fallback:', e.message);
        // Create a fallback storage object
        originalLocalStorage = {
            _data: {},
            getItem: function(key) { return this._data[key] || null; },
            setItem: function(key, value) { this._data[key] = String(value); },
            removeItem: function(key) { delete this._data[key]; },
            clear: function() { this._data = {}; },
            key: function(index) { return Object.keys(this._data)[index] || null; },
            get length() { return Object.keys(this._data).length; }
        };
    }

    // Create safeStorage proxy with error handling
    let safeStorage;
    try {
        safeStorage = new Proxy(originalLocalStorage, {
            get(target, prop) {
                if (prop === 'getItem' || prop === 'setItem' || prop === 'removeItem' || prop === 'clear' || prop === 'key') {
                    return function(...args) {
                        try {
                            return target[prop].apply(target, args);
                        } catch (e) {
                            console.warn('[Storage]', prop, 'failed:', e.message);
                            if (prop === 'getItem' || prop === 'key') return null;
                            if (prop === 'setItem' || prop === 'removeItem' || prop === 'clear') return false;
                        }
                    };
                }
                return target[prop];
            }
        });
    } catch (e) {
        console.warn('[Storage] Proxy creation failed, using fallback:', e.message);
        safeStorage = originalLocalStorage;
    }

    // Replace localStorage with safeStorage, wrapped in try-catch
    try {
        Object.defineProperty(window, 'localStorage', {
            value: safeStorage,
            writable: false,
            configurable: false,
            enumerable: true
        });
        console.log('[Storage] Safe localStorage initialized');
    } catch (e) {
        console.warn('[Storage] Object.defineProperty failed:', e.message);
        // Fallback: directly assign if defineProperty fails
        try {
            window.localStorage = safeStorage;
            console.log('[Storage] Safe localStorage initialized (direct assignment)');
        } catch (e2) {
            console.error('[Storage] All initialization methods failed:', e2.message);
        }
    }
})();
