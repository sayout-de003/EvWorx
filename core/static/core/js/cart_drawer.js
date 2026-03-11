/**
 * Cart Drawer Logic
 */
document.addEventListener('DOMContentLoaded', function() {
    const drawer = document.getElementById('cart-drawer');
    const overlay = document.getElementById('cart-drawer-overlay');
    const closeBtn = document.getElementById('close-cart-drawer');
    const itemsContainer = document.getElementById('cart-drawer-items');
    const totalDisplay = document.getElementById('cart-drawer-total');
    const itemTemplate = document.getElementById('cart-item-template');

    // --- State management ---
    
    function openDrawer() {
        overlay.classList.remove('hidden');
        setTimeout(() => overlay.classList.add('opacity-100'), 10);
        drawer.classList.remove('translate-x-full');
        document.body.classList.add('overflow-hidden');
        document.body.classList.add('cart-open');
    }

    function closeDrawer() {
        overlay.classList.remove('opacity-100');
        drawer.classList.add('translate-x-full');
        setTimeout(() => {
            overlay.classList.add('hidden');
            document.body.classList.remove('cart-open');
        }, 300);
        document.body.classList.remove('overflow-hidden');
    }

    // --- API Interactions ---

    async function fetchCart() {
        try {
            const response = await fetch('/cart/api/', {
                method: 'GET',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            renderCart(data);
        } catch (error) {
            console.error('Error fetching cart:', error);
        }
    }

    async function updateCart(action, productId, quantity = 1) {
        try {
            const response = await fetch('/cart/api/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ action, product_id: productId, quantity })
            });
            const data = await response.json();
            if (data.success) {
                renderCart(data);
                if (action === 'add') openDrawer();
            } else {
                alert(data.message || 'Error updating cart');
            }
        } catch (error) {
            console.error('Error updating cart:', error);
        }
    }

    // --- Rendering ---

    function renderCart(data) {
        itemsContainer.innerHTML = '';
        totalDisplay.innerText = `₹${data.total_price.toFixed(2)}`;

        // Update cart counter (if exists in header)
        const cartCounters = document.querySelectorAll('.cart-count');
        cartCounters.forEach(counter => {
            counter.innerText = data.cart_count;
            if (data.cart_count > 0) {
                counter.classList.remove('hidden');
            } else {
                counter.classList.add('hidden');
            }
        });

        if (data.items.length === 0) {
            itemsContainer.innerHTML = `
                <div class="flex flex-col items-center justify-center h-40 text-gray-500">
                    <i class="fas fa-shopping-cart text-4xl mb-2"></i>
                    <p>Your cart is empty</p>
                </div>
            `;
            return;
        }

        data.items.forEach(item => {
            const clone = itemTemplate.content.cloneNode(true);
            
            // Image
            const img = clone.querySelector('.cart-item-image');
            img.src = item.image_url || 'https://via.placeholder.com/80';
            img.alt = item.title;
            
            // Title
            clone.querySelector('.cart-item-title').innerText = item.title;
            
            // Price & Qty
            clone.querySelector('.cart-item-price').innerText = `₹${item.subtotal.toFixed(2)}`;
            clone.querySelector('.cart-item-qty').innerText = item.quantity;
            
            // Event Listeners
            clone.querySelector('.qty-minus').addEventListener('click', () => {
                updateCart('update', item.product_id, item.quantity - 1);
            });
            
            clone.querySelector('.qty-plus').addEventListener('click', () => {
                updateCart('update', item.product_id, item.quantity + 1);
            });
            
            clone.querySelector('.remove-item').addEventListener('click', () => {
                updateCart('delete', item.product_id);
            });
            
            itemsContainer.appendChild(clone);
        });
    }

    // --- Event Listeners ---

    closeBtn.addEventListener('click', closeDrawer);
    overlay.addEventListener('click', closeDrawer);

    // Global listener for "Add to Cart" forms (event delegation)
    document.addEventListener('submit', function(e) {
        if (e.target.matches('form[action$="/cart/"]')) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const productId = formData.get('product_id');
            const quantity = formData.get('quantity') || 1;
            updateCart('add', productId, parseInt(quantity));
        }
        // Handle forms that might use names instead of slugs in URLs if any
        if (e.target.classList.contains('ajax-cart-form')) {
            e.preventDefault();
            const productId = e.target.querySelector('[name="product_id"]').value;
            const quantity = e.target.querySelector('[name="quantity"]')?.value || 1;
            updateCart('add', productId, parseInt(quantity));
        }
    });

    // Helper: Get CSRF Token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initial cart fetch
    fetchCart();
    
    // Export toggle for global use if needed
    window.toggleCartDrawer = function() {
        if (drawer.classList.contains('translate-x-full')) {
            openDrawer();
        } else {
            closeDrawer();
        }
    };
});
