// Dictionary data storage
const defaultDictionary = {
    "merhaba": {
        word: "merhaba",
        definition: "Selamlaşma sözü, selam.",
        example: "Sabahları komşularıma 'merhaba' diyerek selamlarım.",
        related: ["selam", "günaydın", "iyi günler"],
        category: "isim"
    },
    "kitap": {
        word: "kitap",
        definition: "Basılmış veya yazılmış kâğıtların bir araya getirilip ciltlenmesiyle oluşan, bilgi ve düşünce aktarmaya yarayan nesne.",
        example: "Her gün akşam bir saat kitap okurum.",
        related: ["okuma", "yazar", "kütüphane", "dergi"],
        category: "isim"
    },
    "okuma": {
        word: "okuma",
        definition: "Yazılı bir metni gözden geçirerek anlama işi.",
        example: "Okuma alışkanlığı geliştirmek için düzenli pratik yapmak gerekir.",
        related: ["kitap", "yazma", "öğrenme"],
        category: "isim"
    },
    "yazma": {
        word: "yazma",
        definition: "Düşünceleri, bilgileri yazı ile ifade etme işi.",
        example: "Günlük yazma alışkanlığı düşünceleri netleştirmeye yardımcı olur.",
        related: ["okuma", "kalem", "defter"],
        category: "isim"
    },
    "öğrenme": {
        word: "öğrenme",
        definition: "Bilgi, beceri veya davranış kazanma süreci.",
        example: "Sürekli öğrenme başarının anahtarıdır.",
        related: ["okuma", "eğitim", "bilgi", "öğretmen"],
        category: "isim"
    },
    "eğitim": {
        word: "eğitim",
        definition: "Bireyin davranışlarında kendi yaşantısı yoluyla kasıtlı olarak istendik değişme meydana getirme süreci.",
        example: "Kaliteli eğitim toplumların gelişmesi için çok önemlidir.",
        related: ["öğrenme", "okul", "öğretmen", "öğrenci"],
        category: "isim"
    },
    "bilgisayar": {
        word: "bilgisayar",
        definition: "Verileri işleyen, saklayan ve sonuç üreten elektronik aygıt.",
        example: "Günlük işlerimin çoğunu bilgisayar ile yaparım.",
        related: ["teknoloji", "yazılım", "internet", "programlama"],
        category: "isim"
    },
    "teknoloji": {
        word: "teknoloji",
        definition: "Bilimsel bilgilerin pratik amaçlarla kullanılması, uygulanması.",
        example: "Teknoloji her geçen gün daha da gelişiyor.",
        related: ["bilgisayar", "internet", "yenilik", "gelişim"],
        category: "isim"
    },
    "internet": {
        word: "internet",
        definition: "Dünya çapında birbirine bağlı bilgisayar ağları sistemi.",
        example: "İnternet sayesinde dünyanın her yerindeki insanlarla iletişim kurabiliriz.",
        related: ["bilgisayar", "teknoloji", "web", "iletişim"],
        category: "isim"
    },
    "iletişim": {
        word: "iletişim",
        definition: "Duygu, düşünce veya bilgilerin akması, bildirişim.",
        example: "İyi iletişim her ilişkinin temelidir.",
        related: ["konuşma", "yazma", "telefon", "internet"],
        category: "isim"
    }
};

// Initialize dictionary data
let dictionaryData = {};

// Load data from localStorage or use default
function loadDictionary() {
    const saved = localStorage.getItem('mtuDictionary');
    if (saved) {
        try {
            dictionaryData = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading dictionary:', e);
            dictionaryData = { ...defaultDictionary };
        }
    } else {
        dictionaryData = { ...defaultDictionary };
    }
}

// Save dictionary to localStorage
function saveDictionary() {
    try {
        localStorage.setItem('mtuDictionary', JSON.stringify(dictionaryData));
        return true;
    } catch (e) {
        console.error('Error saving dictionary:', e);
        return false;
    }
}

// Export functions
function getDictionary() {
    return dictionaryData;
}

function getWord(word) {
    const normalized = word.toLowerCase().trim();
    return dictionaryData[normalized];
}

function addWord(wordData) {
    const normalized = wordData.word.toLowerCase().trim();
    dictionaryData[normalized] = wordData;
    saveDictionary();
    return true;
}

function updateWord(word, wordData) {
    const normalized = word.toLowerCase().trim();
    if (dictionaryData[normalized]) {
        dictionaryData[normalized] = wordData;
        saveDictionary();
        return true;
    }
    return false;
}

function deleteWord(word) {
    const normalized = word.toLowerCase().trim();
    if (dictionaryData[normalized]) {
        delete dictionaryData[normalized];
        saveDictionary();
        return true;
    }
    return false;
}

function searchWords(query) {
    const normalized = query.toLowerCase().trim();
    const results = [];
    
    for (const key in dictionaryData) {
        if (key.includes(normalized) || 
            dictionaryData[key].definition.toLowerCase().includes(normalized)) {
            results.push(dictionaryData[key]);
        }
    }
    
    return results;
}

function getWordCount() {
    return Object.keys(dictionaryData).length;
}

// Initialize on load
loadDictionary();
