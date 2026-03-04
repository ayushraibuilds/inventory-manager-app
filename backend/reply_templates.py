"""
Multilingual reply templates for WhatsApp responses.

Currently ships with Hindi (hi) and English (en).
Other languages (ta, te, kn, bn) have stub templates that fall back to English.
"""

TEMPLATES = {
    "en": {
        "ADD": "✅ Added: {items}.\nYour catalog now has {count} items.",
        "ADD_SIMPLE": "✅ Catalog updated. You now have {count} items.",
        "UPDATE": "✅ Item updated successfully.",
        "DELETE": "🗑️ Item removed from your catalog.",
        "UNKNOWN": (
            '🤔 Sorry, I couldn\'t understand that. Try something like:\n'
            '• "Add 10 kg atta at 450 rupees"\n'
            '• "Remove Maggi from my catalog"\n'
            '• "Update rice price to 60 rupees"'
        ),
        "RATE_LIMITED": "⏳ You're sending messages too quickly! Please wait a moment before sending another update.",
        "ONBOARDING": (
            "🎉 *Welcome to ONDC Super Seller!*\n\n"
            "I'm your AI catalog assistant. Just tell me what you sell in Hindi or English:\n\n"
            '• "10 kg atta for 450 rupees"\n'
            '• "5 packet Maggi at 60 each"\n\n'
            "I'll create your ONDC catalog automatically! 📱\n\n"
            "_Tip: Visit the dashboard to set your store name and address._"
        ),
        "ERROR": "⚠️ Sorry, our AI is currently experiencing high traffic. Please try again in a moment.",
        "VOICE_ERROR": "⚠️ We couldn't transcribe your voice note. Please send a text message instead.",
        "UNREGISTERED": "⚠️ Welcome! To create an ONDC catalog, please sign up through our Super Seller Dashboard and link your phone number first.",
        "FAQ": "ℹ️ {answer}",
    },
    "hi": {
        "ADD": "✅ जोड़ा गया: {items}।\nआपके कैटलॉग में अब {count} आइटम हैं।",
        "ADD_SIMPLE": "✅ कैटलॉग अपडेट हो गया। अब {count} आइटम हैं।",
        "UPDATE": "✅ आइटम सफलतापूर्वक अपडेट हो गया।",
        "DELETE": "🗑️ आइटम आपके कैटलॉग से हटा दिया गया।",
        "UNKNOWN": (
            '🤔 माफ करें, मैं समझ नहीं पाया। ऐसे बोलें:\n'
            '• "10 kilo atta 450 mein rakh do"\n'
            '• "Maggi hata do"\n'
            '• "Chawal ka price 60 karo"'
        ),
        "RATE_LIMITED": "⏳ आप बहुत तेज़ी से मैसेज भेज रहे हैं! कृपया थोड़ा रुकें।",
        "ONBOARDING": (
            "🎉 *ONDC Super Seller में आपका स्वागत है!*\n\n"
            "मैं आपका AI कैटलॉग असिस्टेंट हूँ। बस बताइए आप क्या बेचते हैं:\n\n"
            '• "10 kilo atta 450 mein rakh do"\n'
            '• "5 packet Maggi 60 wala"\n\n'
            "मैं आपका ONDC कैटलॉग अपने आप बना दूँगा! 📱\n\n"
            "_टिप: अपनी दुकान का नाम और पता सेट करने के लिए डैशबोर्ड पर जाएं।_"
        ),
        "ERROR": "⚠️ माफ करें, हमारा AI अभी व्यस्त है। कृपया कुछ देर बाद कोशिश करें।",
        "VOICE_ERROR": "⚠️ हम आपका वॉइस नोट नहीं समझ पाए। कृपया टेक्स्ट मैसेज भेजें।",
        "UNREGISTERED": "⚠️ स्वागत है! ONDC कैटलॉग बनाने के लिए, पहले Super Seller Dashboard पर साइनअप करें और अपना फोन नंबर लिंक करें।",
        "FAQ": "ℹ️ {answer}",
    },
    # --- Stub templates for future languages (fall back to English) ---
    "ta": {},
    "te": {},
    "kn": {},
    "bn": {},
}


# Pre-built FAQ answers (English + Hindi)
FAQ_ANSWERS = {
    "en": {
        "how_to_use": (
            "📱 *How to use ONDC Super Seller:*\n\n"
            "Just send me a WhatsApp message describing your products:\n"
            '• "Add 10 kg atta at 450 rupees"\n'
            '• "Remove Maggi"\n'
            '• "Update rice price to 60"\n\n'
            "I'll manage your ONDC catalog automatically!"
        ),
        "pricing": "💰 ONDC Super Seller is currently *free* during our beta period! No charges for catalog management.",
        "ondc": (
            "🇮🇳 *ONDC (Open Network for Digital Commerce)* is India's government-backed open e-commerce network.\n\n"
            "It lets small shopkeepers sell online without depending on a single platform like Amazon or Flipkart.\n\n"
            "Super Seller helps you get listed on ONDC through WhatsApp!"
        ),
        "help": (
            "🆘 *Need help?* Here's what I can do:\n\n"
            "• Add products to your catalog\n"
            "• Update prices and stock\n"
            "• Remove items\n"
            "• Accept voice notes in Hindi/English\n\n"
            "Just send a message describing what you want to do!"
        ),
    },
    "hi": {
        "how_to_use": (
            "📱 *ONDC Super Seller कैसे इस्तेमाल करें:*\n\n"
            "बस मुझे WhatsApp पर अपने प्रोडक्ट के बारे में बताइए:\n"
            '• "10 kilo atta 450 mein rakh do"\n'
            '• "Maggi hata do"\n'
            '• "Chawal ka price 60 karo"\n\n'
            "मैं आपका ONDC कैटलॉग खुद मैनेज कर दूँगा!"
        ),
        "pricing": "💰 ONDC Super Seller अभी *बिल्कुल फ्री* है! कैटलॉग मैनेजमेंट के लिए कोई चार्ज नहीं।",
        "ondc": (
            "🇮🇳 *ONDC* भारत सरकार का ओपन ई-कॉमर्स नेटवर्क है।\n\n"
            "इससे छोटे दुकानदार Amazon या Flipkart पर निर्भर हुए बिना ऑनलाइन बेच सकते हैं।\n\n"
            "Super Seller आपको WhatsApp के ज़रिए ONDC पर लिस्ट करता है!"
        ),
        "help": (
            "🆘 *मदद चाहिए?* मैं ये सब कर सकता हूँ:\n\n"
            "• प्रोडक्ट कैटलॉग में जोड़ना\n"
            "• प्राइस और स्टॉक अपडेट करना\n"
            "• आइटम हटाना\n"
            "• हिंदी/इंग्लिश वॉइस नोट समझना\n\n"
            "बस बताइए आपको क्या करना है!"
        ),
    },
}


def format_reply(lang_code: str, intent: str, **kwargs) -> str:
    """
    Format a reply using the appropriate language template.
    Falls back to English if the language or intent isn't available.
    """
    lang_templates = TEMPLATES.get(lang_code, {})
    # Fall back to English if template not found for this language
    template = lang_templates.get(intent) or TEMPLATES["en"].get(intent, "")
    if not template:
        return ""
    try:
        return template.format(**kwargs)
    except (KeyError, IndexError):
        # If format args are missing, return template as-is
        return template


def get_faq_answer(lang_code: str, topic: str) -> str:
    """Get a localized FAQ answer for the given topic."""
    lang_faqs = FAQ_ANSWERS.get(lang_code, FAQ_ANSWERS["en"])
    return lang_faqs.get(topic, FAQ_ANSWERS["en"].get(topic, ""))
