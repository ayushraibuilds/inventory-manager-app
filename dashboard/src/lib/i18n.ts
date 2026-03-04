const translations: Record<string, Record<string, string>> = {
    en: {
        "nav.dashboard": "ONDC Super Seller",
        "nav.analytics": "Analytics",
        "nav.pricing": "Pricing",
        "nav.orders": "Orders",
        "nav.import": "Import",
        "nav.export": "Export",
        "nav.profile": "Profile",
        "nav.logout": "Logout",
        "stats.totalProducts": "Total Products",
        "stats.totalValue": "Total Value",
        "stats.lowStock": "Low Stock",
        "table.name": "Product Name",
        "table.price": "Price",
        "table.quantity": "Quantity",
        "table.unit": "Unit",
        "table.actions": "Actions",
        "table.noProducts": "No products found",
        "table.addFirst": "Start by adding your first product!",
        "actions.add": "Add Product",
        "actions.edit": "Edit",
        "actions.delete": "Delete",
        "actions.refresh": "Refresh",
        "actions.search": "Search products...",
        "price.competitive": "Competitive",
        "price.above": "Above Market",
        "price.below": "Below Market",
        "price.matchAll": "Match Market Prices",
        "price.intelligence": "Price Intelligence",
        "notifications.title": "Notifications",
        "notifications.empty": "No notifications yet",
        "theme.auto": "Auto",
        "theme.dark": "Dark",
        "theme.light": "Light",
        "ondc.sandbox": "ONDC Sandbox",
        "ondc.offline": "ONDC Offline",
        "ondc.connecting": "Connecting...",
    },
    hi: {
        "nav.dashboard": "ONDC सुपर सेलर",
        "nav.analytics": "विश्लेषण",
        "nav.pricing": "मूल्य निर्धारण",
        "nav.orders": "ऑर्डर",
        "nav.import": "आयात",
        "nav.export": "निर्यात",
        "nav.profile": "प्रोफ़ाइल",
        "nav.logout": "लॉगआउट",
        "stats.totalProducts": "कुल उत्पाद",
        "stats.totalValue": "कुल मूल्य",
        "stats.lowStock": "कम स्टॉक",
        "table.name": "उत्पाद नाम",
        "table.price": "मूल्य",
        "table.quantity": "मात्रा",
        "table.unit": "इकाई",
        "table.actions": "कार्रवाई",
        "table.noProducts": "कोई उत्पाद नहीं मिला",
        "table.addFirst": "अपना पहला उत्पाद जोड़कर शुरू करें!",
        "actions.add": "उत्पाद जोड़ें",
        "actions.edit": "संपादित करें",
        "actions.delete": "हटाएं",
        "actions.refresh": "रिफ्रेश",
        "actions.search": "उत्पाद खोजें...",
        "price.competitive": "प्रतिस्पर्धी",
        "price.above": "बाज़ार से ऊपर",
        "price.below": "बाज़ार से नीचे",
        "price.matchAll": "बाज़ार मूल्य मिलाएं",
        "price.intelligence": "मूल्य बुद्धिमत्ता",
        "notifications.title": "सूचनाएं",
        "notifications.empty": "कोई सूचना नहीं",
        "theme.auto": "स्वचालित",
        "theme.dark": "डार्क",
        "theme.light": "लाइट",
        "ondc.sandbox": "ONDC सैंडबॉक्स",
        "ondc.offline": "ONDC ऑफ़लाइन",
        "ondc.connecting": "कनेक्ट हो रहा है...",
    },
};

export type Lang = "en" | "hi";

export function t(key: string, lang: Lang = "en"): string {
    return translations[lang]?.[key] || translations.en[key] || key;
}

export function getStoredLang(): Lang {
    if (typeof window === "undefined") return "en";
    return (localStorage.getItem("ondc-lang") as Lang) || "en";
}

export function setStoredLang(lang: Lang) {
    localStorage.setItem("ondc-lang", lang);
}
