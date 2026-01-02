// Turkish Translation / Türkçe Çeviri

const tr = {
    title: "🎬 Rockstar Editor Clip Düzenleyici",
    subtitle: "WaydeTheKiwi tarafından oluşturulan, Quadria tarafından geliştirilen GTA V Klip Düzenleyici",
    clipLocation: "Clip dosyalarınıza şu konumdan erişebilirsiniz:",
    clipPath: "YOURPC\\AppData\\Local\\Rockstar Games\\GTA V\\videos\\clip",
    crashInfo: "Oyun içerisinde çektiğiniz bir klibi düzenlerken crash problemi yaşandığında, klibi kurtarmanız için ilgili mapi, scripti ya da aracı kaldırmanıza veya başka bir kaynakla değiştirmenize yarar.",
    fileLabel: "📁 Clip Dosyalarını Seç",
    fileText: ".clip dosyalarını seç veya sürükle-bırak",
    patternsLabel: "📝 Hata veren kaynaklar (Her satıra bir kaynak adı)",
    patternsHelper: "Lütfen çöken kaynakların adlarını buraya sırayla yazın.",
    patternsPlaceholder: `Bulunup değiştirilecek resource adını girin
Örn.
qua_delperroproject_venny
dpemotes
asea`,
    optionsLabel: "⚙️ Seçenekler",
    modeLabel: "Mod:",
    modeNull: "Çöken Kaynaklar",
    modePlaceholder: "Bul ve Değiştir",
    caseInsensitive: "Büyük/Küçük Harf Duyarsız",
    placeholderLabel: "Değişen Resource Adı:",
    startButton: "🚀 Düzenlemeyi Başlat",
    logLabel: "📋 Durum",

    // Messages / Mesajlar
    filesSelected: "dosya seçildi",
    noFilesError: "Lütfen en az bir .clip dosyası seçin.",
    noPatternsError: "Lütfen en az bir clip seçin.",
    processing: "⏳ İşleniyor...",
    found: "Bulundu",
    clipFiles: "clip dosya(s)",
    patterns: "Pattern'ler:",
    mode: "Mod:",
    done: "✅ Tamamlandı! Düzenlenen dosyalar:",
    totalPatterns: "   Toplam temizlenen kaynak:",
    noMatches: "eşleşme yok",
    patternsPatched: "adet hata temizlendi veya düzeltildi",
    ready: "✓ Clip düzenlemeye hazır!",
    completionMessage: (patched, total, patterns) =>
        `Düzenleme tamamlandı!\n\nDüzenlenen dosyalar: ${patched}/${total}\nDüzenlenen kaynaklar: ${patterns}\n\nDeğiştirilmiş dosyalar otomatik olarak indirilecek.`,
    at: "konumunda",
    offset: "offset"
};