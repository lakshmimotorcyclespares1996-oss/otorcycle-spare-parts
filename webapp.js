// Simplified webapp.js that works
console.log('🚀 Loading simplified webapp...');

// Global variables for better state management
let currentUser = { id: 123456, first_name: 'Test User', username: 'testuser' };
let cart = {};
let parts = [];
let filteredParts = [];
let filters = {};
let isRendering = false;
let lastRenderTime = 0;

// Debouncing variables
let filterTimeout = null;
let searchTimeout = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Web app initializing...');
    initializeApp();
    setupEventListeners();
    loadFilters();
    loadParts();
    console.log('✅ Web app initialization complete');
});

function initializeApp() {
    console.log('🚀 Initializing app...');
    
    // Update profile button with user name
    const profileBtn = document.getElementById('profileBtn');
    if (profileBtn && currentUser) {
        profileBtn.textContent = `👤 ${currentUser.first_name || 'Profile'}`;
    }
    
    // Initialize cart count
    updateCartCount();
}

function setupEventListeners() {
    console.log('🔧 Setting up event listeners...');
    
    // Search input with aggressive debouncing
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            // Clear previous timeout
            if (searchTimeout) {
                clearTimeout(searchTimeout);
            }
            
            // Debounce search with longer delay
            searchTimeout = setTimeout(() => {
                filterAndRenderParts();
            }, 500); // Increased to 500ms for smoother experience
        });
    }
    
    // Filter dropdowns with model population
    const categoryFilter = document.getElementById('categoryFilter');
    const brandFilter = document.getElementById('brandFilter');
    const modelFilter = document.getElementById('modelFilter');
    const yearFilter = document.getElementById('yearFilter');
    
    if (categoryFilter) categoryFilter.addEventListener('change', filterAndRenderParts);
    if (brandFilter) {
        brandFilter.addEventListener('change', async function(e) {
            const selectedBrand = e.target.value;
            
            // Populate models for selected brand
            if (selectedBrand && modelFilter) {
                try {
                    const response = await fetch(`/api/models/${selectedBrand}`);
                    if (response.ok) {
                        const data = await response.json();
                        modelFilter.innerHTML = '<option value="">All Models</option>';
                        data.models.forEach(model => {
                            modelFilter.innerHTML += `<option value="${model}">${model}</option>`;
                        });
                    }
                } catch (error) {
                    console.error('Error loading models:', error);
                }
            } else if (modelFilter) {
                modelFilter.innerHTML = '<option value="">All Models</option>';
            }
            
            filterAndRenderParts();
        });
    }
    if (modelFilter) modelFilter.addEventListener('change', filterAndRenderParts);
    if (yearFilter) yearFilter.addEventListener('change', filterAndRenderParts);
    
    // Modal event listeners
    setupModalListeners();
}

function setupModalListeners() {
    // Profile modal
    const profileBtn = document.getElementById('profileBtn');
    const profileModal = document.getElementById('profileModal');
    const closeProfile = document.getElementById('closeProfile');
    
    if (profileBtn && profileModal) {
        profileBtn.addEventListener('click', () => {
            profileModal.style.display = 'block';
            loadUserProfile();
        });
    }
    
    if (closeProfile && profileModal) {
        closeProfile.addEventListener('click', () => {
            profileModal.style.display = 'none';
        });
    }
    
    // Cart modal
    const cartBtn = document.getElementById('cartBtn');
    const cartModal = document.getElementById('cartModal');
    const closeCart = document.getElementById('closeCart');
    
    if (cartBtn && cartModal) {
        cartBtn.addEventListener('click', () => {
            cartModal.style.display = 'block';
            loadCart();
        });
    }
    
    if (closeCart && cartModal) {
        closeCart.addEventListener('click', () => {
            cartModal.style.display = 'none';
        });
    }
    
    // Chat modal
    const chatBtn = document.getElementById('chatBtn');
    const chatModal = document.getElementById('chatModal');
    const closeChat = document.getElementById('closeChat');
    
    if (chatBtn && chatModal) {
        chatBtn.addEventListener('click', () => {
            chatModal.style.display = 'block';
        });
    }
    
    if (closeChat && chatModal) {
        closeChat.addEventListener('click', () => {
            chatModal.style.display = 'none';
        });
    }
    
    // Checkout modal
    const checkoutBtn = document.getElementById('checkoutBtn');
    const checkoutModal = document.getElementById('checkoutModal');
    const closeCheckout = document.getElementById('closeCheckout');
    
    if (checkoutBtn && checkoutModal) {
        checkoutBtn.addEventListener('click', () => {
            checkoutModal.style.display = 'block';
            renderOrderSummary();
        });
    }
    
    if (closeCheckout && checkoutModal) {
        closeCheckout.addEventListener('click', () => {
            checkoutModal.style.display = 'none';
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', function(event) {
        const modals = ['profileModal', 'cartModal', 'chatModal', 'checkoutModal', 'imageModal'];
        modals.forEach(modalId => {
            const modal = document.getElementById(modalId);
            if (modal && event.target === modal) {
                modal.style.display = 'none';
            }
        });
    });
    
    // Image modal event listeners
    setupImageModal();
}

function setupImageModal() {
    const imageModal = document.getElementById('imageModal');
    const closeImageModal = document.getElementById('closeImageModal');
    const modalImage = document.getElementById('modalImage');
    const modalImageTitle = document.getElementById('modalImageTitle');
    const modalImageDetails = document.getElementById('modalImageDetails');
    
    if (closeImageModal && imageModal) {
        closeImageModal.addEventListener('click', () => {
            imageModal.style.display = 'none';
        });
    }
    
    // Close modal when clicking on the image itself
    if (modalImage && imageModal) {
        modalImage.addEventListener('click', () => {
            imageModal.style.display = 'none';
        });
    }
    
    // Close modal with Escape key
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && imageModal && imageModal.style.display === 'block') {
            imageModal.style.display = 'none';
        }
    });
}

function openImageModal(imageSrc, partName, partDetails) {
    const imageModal = document.getElementById('imageModal');
    const modalImage = document.getElementById('modalImage');
    const modalImageTitle = document.getElementById('modalImageTitle');
    const modalImageDetails = document.getElementById('modalImageDetails');
    
    if (imageModal && modalImage && modalImageTitle && modalImageDetails) {
        modalImage.src = imageSrc;
        modalImage.alt = partName;
        modalImageTitle.textContent = partName;
        modalImageDetails.textContent = partDetails;
        imageModal.style.display = 'block';
    }
}

// Load filters
async function loadFilters() {
    console.log('📋 Loading filters...');
    try {
        const response = await fetch('/api/filters');
        if (response.ok) {
            filters = await response.json();
            console.log('✅ Filters loaded:', filters);
            populateFilterDropdowns();
        } else {
            console.error('❌ Filters failed:', response.status);
        }
    } catch (error) {
        console.error('❌ Filters error:', error);
    }
}

function populateFilterDropdowns() {
    // Populate brand filter
    const brandFilter = document.getElementById('brandFilter');
    if (brandFilter && filters.brands) {
        brandFilter.innerHTML = '<option value="">All Brands</option>';
        filters.brands.forEach(brand => {
            brandFilter.innerHTML += `<option value="${brand}">${brand}</option>`;
        });
    }
    
    // Populate category filter
    const categoryFilter = document.getElementById('categoryFilter');
    if (categoryFilter && filters.categories) {
        categoryFilter.innerHTML = '<option value="">All Categories</option>';
        filters.categories.forEach(category => {
            categoryFilter.innerHTML += `<option value="${category}">${category}</option>`;
        });
    }
    
    // Populate year filter
    const yearFilter = document.getElementById('yearFilter');
    if (yearFilter && filters.years) {
        yearFilter.innerHTML = '<option value="">All Years</option>';
        filters.years.forEach(year => {
            yearFilter.innerHTML += `<option value="${year}">${year}</option>`;
        });
    }
    
    // Populate model filter (initially empty, will be populated when brand is selected)
    const modelFilter = document.getElementById('modelFilter');
    if (modelFilter) {
        modelFilter.innerHTML = '<option value="">All Models</option>';
    }
}

// Load parts
async function loadParts() {
    console.log('📦 Loading parts...');
    const partsGrid = document.getElementById('partsGrid');
    if (partsGrid) {
        partsGrid.innerHTML = '<div class="loading">Loading parts...</div>';
    }
    
    try {
        const response = await fetch('/api/parts?limit=200');
        if (response.ok) {
            const data = await response.json();
            parts = data.parts || [];
            console.log('✅ Parts loaded:', parts.length);
            renderParts(parts);
        } else {
            console.error('❌ Parts failed:', response.status);
            if (partsGrid) {
                partsGrid.innerHTML = `<div class="error">Failed to load parts: HTTP ${response.status}</div>`;
            }
        }
    } catch (error) {
        console.error('❌ Parts error:', error);
        if (partsGrid) {
            partsGrid.innerHTML = `<div class="error">Error loading parts: ${error.message}</div>`;
        }
    }
}

// Improved filtering with better debouncing and state management
function filterAndRenderParts() {
    // Prevent multiple simultaneous renders
    if (isRendering) {
        return;
    }
    
    // Clear previous timeout
    if (filterTimeout) {
        clearTimeout(filterTimeout);
    }
    
    // Debounce with longer delay for smoother experience
    filterTimeout = setTimeout(() => {
        performFiltering();
    }, 200); // Reduced to 200ms for better responsiveness
}

function performFiltering() {
    // Prevent concurrent filtering
    if (isRendering) {
        return;
    }
    
    const searchInput = document.getElementById('searchInput');
    const categoryFilter = document.getElementById('categoryFilter');
    const brandFilter = document.getElementById('brandFilter');
    const modelFilter = document.getElementById('modelFilter');
    const yearFilter = document.getElementById('yearFilter');
    
    const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';
    const selectedCategory = categoryFilter ? categoryFilter.value.trim() : '';
    const selectedBrand = brandFilter ? brandFilter.value.trim() : '';
    const selectedModel = modelFilter ? modelFilter.value.trim() : '';
    const selectedYear = yearFilter ? yearFilter.value.trim() : '';
    
    // Create filter signature to avoid unnecessary re-renders
    const filterSignature = `${searchTerm}|${selectedCategory}|${selectedBrand}|${selectedModel}|${selectedYear}`;
    
    // Skip if same filters as last time
    if (window.lastFilterSignature === filterSignature) {
        return;
    }
    window.lastFilterSignature = filterSignature;
    
    let filtered = [...parts]; // Create a copy to avoid modifying original
    
    // Apply search filter
    if (searchTerm) {
        filtered = filtered.filter(part => 
            (part.name || '').toLowerCase().includes(searchTerm) ||
            (part.brand || '').toLowerCase().includes(searchTerm) ||
            (part.category || '').toLowerCase().includes(searchTerm) ||
            (part.part_number || '').toLowerCase().includes(searchTerm)
        );
    }
    
    // Apply category filter - only if a specific category is selected
    if (selectedCategory && selectedCategory !== '') {
        filtered = filtered.filter(part => part.category === selectedCategory);
    }
    
    // Apply brand filter - only if a specific brand is selected
    if (selectedBrand && selectedBrand !== '') {
        filtered = filtered.filter(part => part.brand === selectedBrand);
    }
    
    // Apply model filter - only if a specific model is selected
    if (selectedModel && selectedModel !== '') {
        filtered = filtered.filter(part => part.model === selectedModel);
    }
    
    // Apply year filter - only if a specific year is selected
    if (selectedYear && selectedYear !== '') {
        const year = parseInt(selectedYear);
        filtered = filtered.filter(part => {
            const yearFrom = parseInt(part.year_from) || 0;
            const yearTo = parseInt(part.year_to) || 9999;
            return year >= yearFrom && year <= yearTo;
        });
    }
    
    console.log(`🔧 Filtered to ${filtered.length} parts`);
    
    // Store filtered results
    filteredParts = filtered;
    
    // Render with throttling
    renderPartsSmooth(filtered);
}

// Smooth rendering function to prevent flickering
function renderPartsSmooth(partsToRender) {
    // Throttle rendering to prevent flickering
    const now = Date.now();
    if (now - lastRenderTime < 100) { // Minimum 100ms between renders
        setTimeout(() => renderPartsSmooth(partsToRender), 100);
        return;
    }
    
    lastRenderTime = now;
    isRendering = true;
    
    try {
        renderParts(partsToRender);
    } finally {
        isRendering = false;
    }
}

// Render parts with improved performance
function renderParts(partsToRender) {
    console.log(`🎨 Rendering ${partsToRender.length} parts...`);
    const partsGrid = document.getElementById('partsGrid');
    
    if (!partsGrid) {
        console.error('Parts grid element not found');
        return;
    }
    
    // Use DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    
    if (partsToRender.length === 0) {
        const noPartsDiv = document.createElement('div');
        noPartsDiv.className = 'no-parts';
        noPartsDiv.innerHTML = `
            <h3>No parts found</h3>
            <p>Try adjusting your search or filters.</p>
        `;
        fragment.appendChild(noPartsDiv);
    } else {
        // Render parts in batches to prevent blocking
        partsToRender.forEach(part => {
            const partCard = createPartCard(part);
            fragment.appendChild(partCard);
        });
    }
    
    // Clear and append in one operation to minimize reflow
    partsGrid.innerHTML = '';
    partsGrid.appendChild(fragment);
    
    console.log(`✅ Rendered ${partsToRender.length} parts successfully`);
}

// Create individual part card element
function createPartCard(part) {
    const imageUrl = part.image_url || 'https://via.placeholder.com/300x200/6c757d/ffffff?text=No+Image';
    const stock = parseInt(part.stock) || 0;
    const price = parseFloat(part.price) || 0;
    
    const partCard = document.createElement('div');
    partCard.className = 'part-card';
    partCard.setAttribute('data-part-id', part.id);
    
    // Create part details for modal
    const partDetails = `${part.brand || 'N/A'} - ${part.category || 'N/A'} | Stock: ${stock > 0 ? stock + ' available' : 'Out of stock'} | Price: ₹${price.toFixed(2)}`;
    
    partCard.innerHTML = `
        <div class="part-image-container">
            <img src="${imageUrl}" 
                 alt="${part.name || 'Part'}" 
                 class="part-image" 
                 onerror="this.src='https://via.placeholder.com/300x200/6c757d/ffffff?text=No+Image'"
                 loading="lazy"
                 onclick="openImageModal('${imageUrl}', '${(part.name || 'Unknown Part').replace(/'/g, '\\\')}', '${partDetails.replace(/'/g, '\\\'')}')"
                 title="Click to view full size">
        </div>
        <div class="part-info">
            <div class="part-name">${part.name || 'Unknown Part'}</div>
            <div class="part-details">
                <div class="part-detail">Brand: ${part.brand || 'N/A'}</div>
                <div class="part-detail">Category: ${part.category || 'N/A'}</div>
                <div class="part-detail">Stock: ${stock > 0 ? stock + ' available' : 'Out of stock'}</div>
            </div>
            <div class="part-price">₹${price.toFixed(2)}</div>
            <div class="part-actions">
                <button class="add-to-cart-btn" onclick="addToCart('${part.id}')" ${stock <= 0 ? 'disabled' : ''}>
                    🛒 Add to Cart
                </button>
            </div>
        </div>
    `;
    
    return partCard;
}

// Add to cart
function addToCart(partId) {
    console.log(`🛒 Adding part ${partId} to cart`);
    
    const part = parts.find(p => p.id === partId);
    if (!part) {
        console.error('Part not found:', partId);
        return;
    }
    
    // Add to cart object
    if (cart[partId]) {
        cart[partId].quantity += 1;
    } else {
        cart[partId] = {
            ...part,
            quantity: 1
        };
    }
    
    updateCartCount();
    
    // Show success message
    showNotification(`${part.name} added to cart!`, 'success');
    
    console.log('Cart updated:', cart);
}

// Update cart count
function updateCartCount() {
    const cartCount = document.getElementById('cartCount');
    if (cartCount) {
        const totalItems = Object.values(cart).reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems;
    }
}

// Load cart
function loadCart() {
    const cartItems = document.getElementById('cartItems');
    const cartTotal = document.getElementById('cartTotal');
    
    if (!cartItems) return;
    
    const cartArray = Object.values(cart);
    
    if (cartArray.length === 0) {
        cartItems.innerHTML = '<div class="empty-cart">Your cart is empty</div>';
        if (cartTotal) cartTotal.textContent = '0';
        return;
    }
    
    let html = '';
    let total = 0;
    
    cartArray.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        
        html += `
            <div class="cart-item">
                <img src="${item.image_url || 'https://via.placeholder.com/80x60'}" alt="${item.name}" class="cart-item-image">
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-details">${item.brand} - ${item.category}</div>
                    <div class="cart-item-price">₹${item.price} x ${item.quantity} = ₹${itemTotal.toFixed(2)}</div>
                </div>
                <button class="remove-from-cart" onclick="removeFromCart('${item.id}')">×</button>
            </div>
        `;
    });
    
    cartItems.innerHTML = html;
    if (cartTotal) cartTotal.textContent = total.toFixed(2);
}

// Remove from cart
function removeFromCart(partId) {
    delete cart[partId];
    updateCartCount();
    loadCart();
    showNotification('Item removed from cart', 'info');
}

// Load user profile
function loadUserProfile() {
    // For now, just populate with current user data
    const fullName = document.getElementById('fullName');
    const phoneNumber = document.getElementById('phoneNumber');
    const address = document.getElementById('address');
    const email = document.getElementById('email');
    
    if (fullName) fullName.value = currentUser.first_name || '';
    if (phoneNumber) phoneNumber.value = '';
    if (address) address.value = '';
    if (email) email.value = '';
}

// Render order summary
function renderOrderSummary() {
    const orderItems = document.getElementById('orderItems');
    const orderTotal = document.getElementById('orderTotal');
    
    if (!orderItems) return;
    
    const cartArray = Object.values(cart);
    let html = '';
    let total = 0;
    
    cartArray.forEach(item => {
        const itemTotal = item.price * item.quantity;
        total += itemTotal;
        
        html += `
            <div class="order-item">
                <span>${item.name} x${item.quantity}</span>
                <span>₹${itemTotal.toFixed(2)}</span>
            </div>
        `;
    });
    
    orderItems.innerHTML = html;
    if (orderTotal) orderTotal.textContent = total.toFixed(2);
}

// Show notification
function showNotification(message, type = 'info') {
    // Simple alert for now - can be enhanced later
    alert(message);
}

// Show loading state
function showLoading(show) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    if (loadingSpinner) {
        loadingSpinner.style.display = show ? 'block' : 'none';
    }
}

console.log('✅ Simplified webapp.js loaded successfully');