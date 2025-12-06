// MTU Zincirli Sözlük - Web JavaScript

// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Close menu when clicking outside
    document.addEventListener('click', function(e) {
        if (navMenu && !e.target.closest('.navbar')) {
            navMenu.classList.remove('active');
        }
    });
});

// API helper functions
const API = {
    baseUrl: '',
    
    async ara(sorgu, limit = 20) {
        const response = await fetch(`${this.baseUrl}/api/ara?q=${encodeURIComponent(sorgu)}&limit=${limit}`);
        return response.json();
    },
    
    async kelime(kelime) {
        const response = await fetch(`${this.baseUrl}/api/kelime/${encodeURIComponent(kelime)}`);
        return response.json();
    },
    
    async benzer(kelime, limit = 15) {
        const response = await fetch(`${this.baseUrl}/api/benzer/${encodeURIComponent(kelime)}?limit=${limit}`);
        return response.json();
    },
    
    async zincir(kelime, derinlik = 3) {
        const response = await fetch(`${this.baseUrl}/api/zincir/${encodeURIComponent(kelime)}?derinlik=${derinlik}`);
        return response.json();
    },
    
    async istatistikler() {
        const response = await fetch(`${this.baseUrl}/api/istatistikler`);
        return response.json();
    },
    
    async tdk(kelime) {
        const response = await fetch(`${this.baseUrl}/api/tdk/${encodeURIComponent(kelime)}`);
        return response.json();
    },
    
    async rastgeleKelime() {
        const response = await fetch(`${this.baseUrl}/api/rastgele-kelime`);
        return response.json();
    },
    
    async kelimeEkle(data) {
        const response = await fetch(`${this.baseUrl}/api/kelime-ekle`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },
    
    async kelimeSil(kelime) {
        const response = await fetch(`${this.baseUrl}/api/kelime-sil/${encodeURIComponent(kelime)}`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// Debounce utility
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Toast notifications
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Copy to clipboard
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showToast('Kopyalandı!', 'success');
    } catch (err) {
        showToast('Kopyalama başarısız', 'error');
    }
}

// Export API for use in other scripts
window.SozlukAPI = API;
