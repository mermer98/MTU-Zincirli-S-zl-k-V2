// DOM Elements
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const addBtn = document.getElementById('addBtn');
const wordDisplay = document.getElementById('wordDisplay');
const wordCount = document.getElementById('wordCount');

// Modal elements
const modal = document.getElementById('wordModal');
const modalTitle = document.getElementById('modalTitle');
const closeBtn = document.querySelector('.close');
const cancelBtn = document.getElementById('cancelBtn');
const wordForm = document.getElementById('wordForm');
const wordInput = document.getElementById('wordInput');
const definitionInput = document.getElementById('definitionInput');
const exampleInput = document.getElementById('exampleInput');
const relatedWordsInput = document.getElementById('relatedWordsInput');
const categoryInput = document.getElementById('categoryInput');

// State
let editMode = false;
let currentWord = null;

// HTML escaping function to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize app
function init() {
    updateWordCount();
    displayWelcomeMessage();
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    });
    addBtn.addEventListener('click', openAddModal);
    closeBtn.addEventListener('click', closeModal);
    closeBtn.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            closeModal();
        }
    });
    cancelBtn.addEventListener('click', closeModal);
    wordForm.addEventListener('submit', handleFormSubmit);
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
}

// Display welcome message
function displayWelcomeMessage() {
    wordDisplay.innerHTML = `
        <div class="no-results">
            <h2>MTU Zincirli Sözlük V2'ye Hoş Geldiniz</h2>
            <p>Kelime aramak için yukarıdaki arama kutusunu kullanabilirsiniz.</p>
            <p>Yeni kelime eklemek için "Yeni Kelime Ekle" butonuna tıklayabilirsiniz.</p>
            <p>İlişkili kelimelere tıklayarak kelimeler arasında gezinebilirsiniz.</p>
        </div>
    `;
}

// Handle search
function handleSearch() {
    const query = searchInput.value.trim();
    if (!query) {
        displayWelcomeMessage();
        return;
    }

    const word = getWord(query);
    if (word) {
        displayWord(word);
    } else {
        displayNoResults(query);
    }
}

// Display word
function displayWord(wordData) {
    const relatedWordsHTML = wordData.related && wordData.related.length > 0
        ? `
            <div class="word-related">
                <h3>İlişkili Kelimeler:</h3>
                <div class="related-words">
                    ${wordData.related.map(w => {
                        const escapedWord = escapeHtml(w);
                        return `<span class="related-word-link" data-word="${escapedWord}">${escapedWord}</span>`;
                    }).join('')}
                </div>
            </div>
        `
        : '';

    const exampleHTML = wordData.example
        ? `<div class="word-example">📝 Örnek: ${escapeHtml(wordData.example)}</div>`
        : '';

    wordDisplay.innerHTML = `
        <div class="word-entry">
            <h2 class="word-title">${escapeHtml(wordData.word)}</h2>
            ${wordData.category ? `<span class="word-category">${escapeHtml(wordData.category)}</span>` : ''}
            <div class="word-definition">${escapeHtml(wordData.definition)}</div>
            ${exampleHTML}
            ${relatedWordsHTML}
        </div>
    `;
    
    // Add event listeners to related word links
    document.querySelectorAll('.related-word-link').forEach(link => {
        link.addEventListener('click', () => {
            searchRelatedWord(link.getAttribute('data-word'));
        });
    });
}

// Display no results
function displayNoResults(query) {
    const escapedQuery = escapeHtml(query);
    wordDisplay.innerHTML = `
        <div class="no-results">
            <h2>Sonuç Bulunamadı</h2>
            <p>"${escapedQuery}" için bir sonuç bulunamadı.</p>
            <p>Yeni kelime eklemek ister misiniz?</p>
            <button class="btn btn-success" data-word="${escapedQuery}">Bu Kelimeyi Ekle</button>
        </div>
    `;
    
    // Add event listener to the button
    const addButton = wordDisplay.querySelector('.btn-success');
    if (addButton) {
        addButton.addEventListener('click', () => {
            openAddModalWithWord(addButton.getAttribute('data-word'));
        });
    }
}

// Search related word
function searchRelatedWord(word) {
    searchInput.value = word;
    handleSearch();
}

// Open add modal
function openAddModal() {
    editMode = false;
    currentWord = null;
    modalTitle.textContent = 'Yeni Kelime Ekle';
    wordForm.reset();
    wordInput.readOnly = false;
    modal.style.display = 'block';
}

// Open add modal with word
function openAddModalWithWord(word) {
    openAddModal();
    wordInput.value = word;
}

// Close modal
function closeModal() {
    modal.style.display = 'none';
    wordForm.reset();
    editMode = false;
    currentWord = null;
}

// Handle form submit
function handleFormSubmit(e) {
    e.preventDefault();

    const wordData = {
        word: wordInput.value.trim(),
        definition: definitionInput.value.trim(),
        example: exampleInput.value.trim(),
        related: relatedWordsInput.value
            .split(',')
            .map(w => w.trim())
            .filter(w => w.length > 0),
        category: categoryInput.value.trim()
    };

    if (editMode && currentWord) {
        updateWord(currentWord, wordData);
        alert('Kelime başarıyla güncellendi!');
    } else {
        addWord(wordData);
        alert('Kelime başarıyla eklendi!');
    }

    closeModal();
    updateWordCount();
    displayWord(wordData);
    searchInput.value = wordData.word;
}

// Update word count
function updateWordCount() {
    wordCount.textContent = getWordCount();
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
