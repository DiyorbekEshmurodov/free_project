SECTION_MAP = {
    'nutrition': {
        'title': "To'g'ri Ovqatlanish Sirlari",
        'subtitle': "Zararli ovqatlanish tartibidan voz keching va to'g'ri ratsion yarating.",
        'questions': {
            'q1': {
                'icon': '🌙',
                'title': 'Kechki ishtaha va tungi ochlik',
                'short_desc': 'Kechasi qorin ochishi va tungi tamaddilarni jilovlash usullari.'
            },
            'q2': {
                'icon': '🍩',
                'title': 'Shirinlik va fastfud qaramligi',
                'short_desc': 'Zararli taomlarga bo\'lgan kuchli xohishni bartaraf etish.'
            },
            'q3': {
                'icon': '⚡',
                'title': 'Parhezda energiya yetishmasligi',
                'short_desc': 'Holsizlikni oldini olish va quvvatni oshirish usullari.'
            },
            'q4': {
                'icon': '💰',
                'title': 'Arzon va hamyonbop menyu',
                'short_desc': 'Katta byudjet talab qilmaydigan balanslashgan taomnoma.'
            }
        }
    },
    'ai_analysis': {
        'title': "AI Orqali Analiz",
        'subtitle': "Sizning tana ko'rsatkichlaringizga asoslangan sun'iy intellekt tahlili.",
        'questions': {
            'q1': {
                'icon': '📊',
                'title': 'Vaznim va bo\'yimga ko\'ra holatim qanday?',
                'short_desc': 'TMI ko\'rsatkichingiz va kunlik kerakli kaloriya miqdorini bilib oling.'
            },
            'q2': {
                'icon': '🥗',
                'title': 'Sog\'lom ozish uchun 1 kunlik menyu tuzib bering',
                'short_desc': 'Vazn tashlashga mo\'ljallangan balansli taomnoma tartibi.'
            },
            'q3': {
                'icon': '💪',
                'title': 'To\'g\'ri semirish va mushak yig\'ish usuli',
                'short_desc': 'Sog\'lom vazn orttirish uchun zaruriy taomlar va tavsiyalar.'
            },
            'q4': {
                'icon': '🏋️‍♂️',
                'title': 'Maqsadimga mos haftalik mashqlar rejasi',
                'short_desc': 'Aynan sizning vazningiz va bo\'yingizga mos mashg\'ulotlar tartibi.'
            }
        }
    },
    'macros': {
        'title': "Kerakli Oqsil va Yog'lar",
        'subtitle': "Kunlik BJU me'yorini to'g'ri hisoblash va sifatli manbalar.",
        'questions': {
            'q1': {
                'icon': '⚖️',
                'title': 'Kunlik oqsil va yog\' me\'yorim qancha?',
                'short_desc': 'Bo\'yingiz va vazningizga mos aniq grammlarda hisoblash.'
            },
            'q2': {
                'icon': '🥩',
                'title': 'Eng sifatli va hamyonbop oqsil manbalari',
                'short_desc': 'Kundalik ratsionga qo\'shish kerak bo\'lgan mahsulotlar ro\'yxati.'
            },
            'q3': {
                'icon': '🥑',
                'title': 'Foydali va zararli yog\'larni qanday ajratamiz?',
                'short_desc': 'Organizm va gormonlar uchun zarur bo\'lgan to\'g\'ri yog\'lar.'
            },
            'q4': {
                'icon': '🔍',
                'title': 'Oqsil tanqisligini qanday bilish mumkin?',
                'short_desc': 'Belgilar va uni bartaraf etish usullari.'
            }
        }
    },
    'advice': {
        'title': "Diyetolog Maslahati",
        'subtitle': "Professional diyetologik yo'riqnomalar va tavsiyalar.",
        'questions': {
            'q1': {
                'icon': '🔥',
                'title': 'Moddalar almashinuvini (metabolizm) tezlashtirish',
                'short_desc': 'Yog\' erishini va energiyani oshiruvchi eng muhim qoidalar.'
            },
            'q2': {
                'icon': '💧',
                'title': 'Kunlik suv me\'yorini to\'g\'ri hisoblash',
                'short_desc': 'Organizm va oshqozon uchun to\'g\'ri suv ichish tartibi.'
            },
            'q3': {
                'icon': '🩺',
                'title': 'Parhez paytida oshqozon-ichak faoliyatini yaxshilash',
                'short_desc': 'Hazm qilishni yengillashtirish va dam bo\'lishni yo\'qotish.'
            },
            'q4': {
                'icon': '🎯',
                'title': 'Tashlangan vaznni qayta olmaslik siri',
                'short_desc': 'Natijani uzoq muddatga saqlab qolish strategiyasi.'
            }
        }
    }
}

def get_question_prompt(section_name, question_id):
    section = SECTION_MAP.get(section_name, {})
    question = section.get('questions', {}).get(question_id, {})
    return f"{question.get('title', '')}: {question.get('short_desc', '')}"