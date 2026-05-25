"""
Тексты сообщений для LINE бота.
Структура идентична Telegram-боту для простоты переноса.
"""

TEXTS = {
    "en": {
        "welcome": "👋 Welcome! Please choose your language:",
        "lang_set": "✅ Language set to English.",
        "main_menu": "🏠 Main Menu\nChoose an option below:",
        "btn_stores": "📍 Find nearest store",
        "btn_loyalty": "🎁 Get loyalty card",
        "btn_manager": "💬 Contact manager",
        "btn_about": "ℹ️ About us",
        "btn_socials": "📲 Our socials",
        "btn_back": "⬅️ Back",
        "btn_main_menu": "🏠 Main menu",
        "btn_change_lang": "🌐 Change language",
        "loading": "⏳ Processing...",
        "help_welcome": (
            "🤖 AI Help Assistant\n\n"
            "Welcome! Feel free to ask any questions.\n"
            "We'll respond as soon as possible!\n\n"
            "Type your question below 👇"
        ),
        "loyalty_hint": "Get your loyalty card in 30 seconds and receive a bonus 🎁",
        # Reminders
        "loyalty_reminder": "It takes 30 seconds to create a loyalty card for bonuses in every store",
        "after_phone_reminder": "Finish registration to activate your bonus",
        "loyalty5m_reminder": "Without registration you can't get rewards in stores",
        "loyalty24h_reminder": "Your bonus -30% is still waiting 🎁. Register to get your loyalty card!",
        # Loyalty flow
        "loyalty_start": (
            "🎁 Get access to bonuses, discounts and faster service\n\n"
            "Please enter your phone number in international format:\n"
            "Example: +66812345678"
        ),
        "loyalty_phone_invalid": "❌ Invalid phone number. Please use international format, e.g. +66812345678",
        "loyalty_otp_sent": "📱 OTP code sent to {phone}\n\nPlease enter the 6-digit code:",
        "loyalty_otp_invalid": "❌ Invalid OTP code. Please try again or type /start to restart.",
        "loyalty_otp_attempts": "❌ Too many failed attempts. Please type /start to restart.",
        "loyalty_ask_name": "✅ Phone verified!\n\nPlease enter your full name:",
        "loyalty_name_invalid": "❌ Please enter your real full name (at least 2 characters):",
        "loyalty_ask_country": "🌍 Please enter your country (e.g. Thailand, Russia, USA):",
        "loyalty_ask_tourist": "🌍 Are you visiting as a tourist?\n\nReply with: yes / no",
        "loyalty_ask_thai_citizen": "🇹🇭 Are you a Thai citizen?\n\nReply with: yes / no",
        "loyalty_yes_no_buttons": True,  # use quick reply buttons
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "loyalty_success": (
            "🎉 Registration successful!\n\n"
            "📱 Phone: {phone}\n"
            "🏷 Your loyalty card barcode: {barcode}\n\n"
            "Show this code at any of our stores to get your discount!"
        ),
        "loyalty_already_exists": (
            "✅ Welcome back!\n\n"
            "📱 Phone: {phone}\n"
            "🏷 Barcode: {barcode}\n\n"
            "Your information has been updated."
        ),
        "loyalty_crm_error": "⚠️ A technical error occurred. Please try again later or contact our manager.",
        "show_card_hint": "\nDon't forget to show your loyalty card in store to get bonus",
        # Store search
        "stores_request_geo": (
            "📍 Find nearest store\n\n"
            "Please share your location or choose a region manually:"
        ),
        "btn_send_geo": "📍 Share my location",
        "btn_choose_region": "🗺 Choose region",
        "stores_choose_region": "Please select your region:",
        "stores_not_found": "😔 No stores found nearby. Try a different region.",
        "stores_result": "📍 Nearest stores ({count} found):",
        "btn_open_maps": "🗺 Google Maps",
        "store_card": "🏪 {name}\n📍 {address}\n🕐 {hours}\n",
        "btn_help": "🤖 AI Help",
        "btn_help_new_chat": "🔄 New chat",
        # Manager
        "manager_hello": (
            "💬 Manager Chat\n\n"
            "Our AI assistant will help you first.\n"
            "Type your question:"
        ),
        "manager_offline": (
            "🕐 Our managers work from 10:00 to 18:00.\n\n"
            "You can leave a message and we'll get back to you:"
        ),
        "manager_transfer": "🔄 Transferring you to a live manager...",
        "manager_transferred": "✅ A manager will respond shortly. Please wait.",
        "manager_username_prompt": "👤 You can contact our manager directly on LINE: {line_id}",
        "manager_left_message": "✅ Your message has been saved. We'll contact you soon!",
        "btn_transfer_manager": "👤 Talk to a human",
        "ai_error": "⚠️ AI assistant is temporarily unavailable. Connecting you to a manager...",
        # About
        "about_text": (
            "ℹ️ About Us\n\n"
            "We are a leading retail company providing quality products.\n\n"
            "🌐 Our stores are located across multiple countries.\n"
            "📞 Support: available 24/7 via this bot.\n\n"
            "Use the menu below to explore more:"
        ),
        # Socials
        "socials_text": "📲 Our Social Media\n\nVisit our mini-landing page for all links:",
        "btn_open_socials": "🔗 Open social links",
        # Errors
        "error_generic": "⚠️ Something went wrong. Please try again.",
    },

    "ru": {
        "welcome": "👋 Добро пожаловать! Пожалуйста, выберите язык:",
        "lang_set": "✅ Язык установлен: Русский.",
        "main_menu": "🏠 Главное меню\nВыберите раздел:",
        "btn_stores": "📍 Найти ближайший магазин",
        "btn_loyalty": "🎁 Получить карту лояльности",
        "btn_manager": "💬 Связаться с менеджером",
        "btn_about": "ℹ️ О компании",
        "btn_socials": "📲 Наши соцсети",
        "btn_back": "⬅️ Назад",
        "btn_main_menu": "🏠 Главное меню",
        "btn_change_lang": "🌐 Сменить язык",
        "loading": "⏳ Загрузка...",
        "help_welcome": (
            "🤖 Помощник ИИ\n\n"
            "Приветствуем!.\n"
            "Задай нам любой вопрос и мы быстро ответим!\n\n"
            "Напишите ваш вопрос ниже 👇"
        ),
        "loyalty_hint": "Получите карту лояльности за 30 секунд и получите бонус 🎁",
        "loyalty_reminder": "Создание карты лояльности для получения бонусов в любом магазине занимает 30 секунд",
        "after_phone_reminder": "Завершите регистрацию, чтобы активировать бонус",
        "loyalty5m_reminder": "Без регистрации вы не сможете получать бонусы в магазинах",
        "loyalty24h_reminder": "Ваш бонус -30% всё ещё ждёт вас 🎁. Зарегистрируйтесь, чтобы получить карту постоянного клиента!",
        "loyalty_start": (
            "🎁 Получите доступ к бонусам, скидкам и более оперативному обслуживанию\n\n"
            "Введите номер телефона в международном формате:\n"
            "Пример: +66812345678"
        ),
        "loyalty_phone_invalid": "❌ Неверный формат номера. Используйте международный формат, например: +66812345678",
        "loyalty_otp_sent": "📱 OTP-код отправлен на {phone}\n\nВведите 6-значный код:",
        "loyalty_otp_invalid": "❌ Неверный OTP-код. Попробуйте ещё раз или напишите /start для перезапуска.",
        "loyalty_otp_attempts": "❌ Слишком много попыток. Напишите /start для перезапуска.",
        "loyalty_ask_name": "✅ Телефон подтверждён!\n\nВведите ваше полное имя:",
        "loyalty_name_invalid": "❌ Введите настоящее имя (минимум 2 символа):",
        "loyalty_ask_country": "🌍 Введите вашу страну (например: Таиланд, Россия, США):",
        "loyalty_ask_tourist": "🌍 Вы приехали как турист?\n\nОтветьте: да / нет",
        "loyalty_ask_thai_citizen": "🇹🇭 Вы гражданин Таиланда?\n\nОтветьте: да / нет",
        "btn_yes": "✅ Да",
        "btn_no": "❌ Нет",
        "btn_help": "🤖 Помощник ИИ",
        "btn_help_new_chat": "🔄 Новый чат",
        "loyalty_success": (
            "🎉 Регистрация успешна!\n\n"
            "📱 Телефон: {phone}\n"
            "🏷 Штрих-код карты лояльности: {barcode}\n\n"
            "Покажите этот код в любом нашем магазине!"
        ),
        "loyalty_already_exists": (
            "✅ Добро пожаловать обратно!\n\n"
            "📱 Телефон: {phone}\n"
            "🏷 Штрих-код: {barcode}\n\n"
            "Ваши данные обновлены."
        ),
        "loyalty_crm_error": "⚠️ Произошла техническая ошибка. Попробуйте позже или свяжитесь с менеджером.",
        "show_card_hint": "\nНе забудьте показать карту лояльности в магазине для получения бонуса",
        "stores_request_geo": "📍 Найти ближайший магазин\n\nПоделитесь геолокацией или выберите регион вручную:",
        "btn_send_geo": "📍 Поделиться геолокацией",
        "btn_choose_region": "🗺 Выбрать регион",
        "stores_choose_region": "Выберите ваш регион:",
        "stores_not_found": "😔 Магазины не найдены. Попробуйте другой регион.",
        "stores_result": "📍 Ближайшие магазины ({count} найдено):",
        "btn_open_maps": "🗺 Google Maps",
        "store_card": "🏪 {name}\n📍 {address}\n🕐 {hours}\n",
        "manager_hello": "💬 Чат с менеджером\n\nНаш AI-ассистент ответит вам первым.\nЗадайте вопрос:",
        "manager_offline": "🕐 Менеджеры работают с 10:00 до 18:00.\n\nОставьте сообщение, и мы свяжемся с вами:",
        "manager_transfer": "🔄 Переключаю на живого менеджера...",
        "manager_transferred": "✅ Менеджер скоро ответит. Пожалуйста, подождите.",
        "manager_username_prompt": "👤 Вы можете написать нашему менеджеру напрямую в LINE: {line_id}",
        "manager_left_message": "✅ Ваше сообщение сохранено. Мы свяжемся с вами!",
        "btn_transfer_manager": "👤 Поговорить с менеджером",
        "ai_error": "⚠️ AI-ассистент временно недоступен. Подключаем менеджера...",
        "about_text": (
            "ℹ️ О нас\n\n"
            "Мы ведущая розничная компания, предлагающая качественные товары.\n\n"
            "📞 Поддержка: доступна 24/7 через этот бот."
        ),
        "socials_text": "📲 Наши социальные сети\n\nПерейдите на нашу страницу со всеми ссылками:",
        "btn_open_socials": "🔗 Открыть соцсети",
        "error_generic": "⚠️ Что-то пошло не так. Попробуйте ещё раз.",
    },

    "th": {
        "welcome": "👋 ยินดีต้อนรับ! กรุณาเลือกภาษา:",
        "lang_set": "✅ ตั้งภาษาเป็นภาษาไทยแล้ว",
        "main_menu": "🏠 เมนูหลัก\nเลือกตัวเลือกด้านล่าง:",
        "btn_stores": "📍 ค้นหาร้านใกล้เคียง",
        "btn_loyalty": "🎁 รับบัตรสะสมแต้ม",
        "btn_manager": "💬 ติดต่อผู้จัดการ",
        "btn_about": "ℹ️ เกี่ยวกับเรา",
        "btn_socials": "📲 โซเชียลของเรา",
        "btn_back": "⬅️ กลับ",
        "btn_main_menu": "🏠 เมนูหลัก",
        "btn_change_lang": "🌐 เปลี่ยนภาษา",
        "loading": "⏳ กำลังประมวลผล...",
        "help_welcome": (
            "🤖 ผู้ช่วย AI\n\n"
            "ยินดีต้อนรับ!\n"
            "หากมีข้อสงสัยใด ๆ โปรดสอบถามได้เลย เราจะตอบกลับโดยเร็วที่สุด!\n\n"
            "พิมพ์คำถามด้านล่าง 👇"
        ),
        "loyalty_hint": "รับบัตรสะสมแต้มใน 30 วินาทีและรับโบนัส 🎁",
        "loyalty_reminder": "ใช้เวลา 30 วินาทีในการสร้างบัตรสะสมแต้มเพื่อรับโบนัสในทุกร้าน",
        "after_phone_reminder": "ลงทะเบียนให้เสร็จสิ้นเพื่อเปิดใช้งานโบนัสของคุณ",
        "loyalty5m_reminder": "หากไม่ลงทะเบียน คุณจะไม่ได้รับรางวัลในร้านค้า",
        "loyalty24h_reminder": "โบนัส -30% ของคุณยังคงรอ 🎁 ลงทะเบียนเพื่อรับบัตรสะสมแต้ม!",
        "loyalty_start": (
            "🎁 รับสิทธิ์เข้าถึงโบนัส ส่วนลด และบริการที่รวดเร็วขึ้น\n\n"
            "กรุณากรอกหมายเลขโทรศัพท์ในรูปแบบสากล:\n"
            "ตัวอย่าง: +66812345678"
        ),
        "loyalty_phone_invalid": "❌ หมายเลขโทรศัพท์ไม่ถูกต้อง กรุณาใช้รูปแบบสากล เช่น +66812345678",
        "loyalty_otp_sent": "📱 ส่งรหัส OTP ไปยัง {phone} แล้ว\n\nกรุณากรอกรหัส 6 หลัก:",
        "loyalty_otp_invalid": "❌ รหัส OTP ไม่ถูกต้อง กรุณาลองใหม่",
        "loyalty_otp_attempts": "❌ ลองมากเกินไป กรุณาเริ่มใหม่ด้วย /start",
        "loyalty_ask_name": "✅ ยืนยันหมายเลขโทรศัพท์แล้ว!\n\nกรุณากรอกชื่อเต็มของคุณ:",
        "loyalty_name_invalid": "❌ กรุณากรอกชื่อจริง (อย่างน้อย 2 ตัวอักษร):",
        "loyalty_ask_country": "🌍 กรุณากรอกประเทศของคุณ (เช่น Thailand, Russia, USA):",
        "loyalty_ask_tourist": "🌍 คุณมาเที่ยวในฐานะนักท่องเที่ยวหรือไม่?\n\nตอบ: ใช่ / ไม่",
        "loyalty_ask_thai_citizen": "🇹🇭 คุณเป็นคนไทยหรือไม่?\n\nตอบ: ใช่ / ไม่",
        "btn_yes": "✅ ใช่",
        "btn_no": "❌ ไม่",
        "loyalty_success": (
            "🎉 ลงทะเบียนสำเร็จ!\n\n"
            "📱 โทรศัพท์: {phone}\n"
            "🏷 บาร์โค้ดบัตรสะสมแต้ม: {barcode}\n\n"
            "แสดงรหัสนี้ที่ร้านค้าของเราเพื่อรับส่วนลด!"
        ),
        "loyalty_already_exists": (
            "✅ ยินดีต้อนรับกลับ!\n\n"
            "📱 โทรศัพท์: {phone}\n"
            "🏷 บาร์โค้ด: {barcode}\n\n"
            "อัปเดตข้อมูลของคุณแล้ว"
        ),
        "loyalty_crm_error": "⚠️ เกิดข้อผิดพลาดทางเทคนิค กรุณาลองใหม่ภายหลัง",
        "show_card_hint": "\nอย่าลืมแสดงบัตรสะสมแต้มที่ร้านเพื่อรับโบนัส",
        "stores_request_geo": "📍 ค้นหาร้านใกล้เคียง\n\nแชร์ตำแหน่งของคุณหรือเลือกภูมิภาค:",
        "btn_send_geo": "📍 แชร์ตำแหน่ง",
        "btn_choose_region": "🗺 เลือกภูมิภาค",
        "stores_choose_region": "เลือกภูมิภาคของคุณ:",
        "stores_not_found": "😔 ไม่พบร้านค้าในบริเวณนี้ ลองภูมิภาคอื่น",
        "stores_result": "📍 ร้านค้าใกล้เคียง ({count} แห่ง):",
        "btn_open_maps": "🗺 Google Maps",
        "store_card": "🏪 {name}\n📍 {address}\n🕐 {hours}\n",
        "manager_hello": "💬 แชทกับผู้จัดการ\n\nผู้ช่วย AI จะตอบคุณก่อน\nพิมพ์คำถามของคุณ:",
        "manager_offline": "🕐 ผู้จัดการทำงานตั้งแต่ 10:00 - 18:00\n\nฝากข้อความได้เลย:",
        "manager_transfer": "🔄 กำลังโอนสายไปยังผู้จัดการ...",
        "manager_transferred": "✅ ผู้จัดการจะตอบในไม่ช้า กรุณารอสักครู่",
        "manager_username_prompt": "👤 คุณสามารถติดต่อผู้จัดการของเราโดยตรงใน LINE: {line_id}",
        "manager_left_message": "✅ บันทึกข้อความแล้ว เราจะติดต่อกลับ!",
        "btn_transfer_manager": "👤 คุยกับคนจริงๆ",
        "ai_error": "⚠️ AI ไม่พร้อมใช้งานชั่วคราว กำลังเชื่อมต่อผู้จัดการ...",
        "btn_help": "🤖 ผู้ช่วย AI",
        "btn_help_new_chat": "🔄 แชทใหม่",

        "about_text": (
            "ℹ️ เกี่ยวกับเรา\n\n"
            "เราเป็นบริษัทค้าปลีกชั้นนำที่มีสินค้าคุณภาพ\n\n"
            "🌐 ร้านค้าของเราอยู่ในหลายประเทศ\n"
            "📞 การสนับสนุน: 24/7 ผ่านบอทนี้"
        ),
        "socials_text": "📲 โซเชียลมีเดียของเรา\n\nเยี่ยมชมหน้าลิงก์ทั้งหมดของเรา:",
        "btn_open_socials": "🔗 เปิดลิงก์โซเชียล",
        "error_generic": "⚠️ เกิดข้อผิดพลาด กรุณาลองใหม่",
    },
}


def t(lang: str, key: str, **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS["en"]).get(key) or TEXTS["en"].get(key, f"[{key}]")
    if kwargs and isinstance(text, str):
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text
