"""
nlp/dataset.py - synthetic training data for the intent classifier.

Real labelled questions in Hindi/Marathi do not exist for this domain, so we generate
them from hand-written templates in five input styles:

    en  English                     hr  Hindi in Roman letters     mr  Marathi in Roman letters
    hd  Hindi in Devanagari         md  Marathi in Devanagari

IMPORTANT (for your report): template data is easy - a model trained on it will score
~100% on templates it has seen. That is why the real test set (nlp/data/intent_test.csv)
is written by hand, with different wording and spellings, and is never used for training.

Run:  python -m nlp.train      (writes nlp/data/intent_train.csv and nlp/models/intent_nb.json)
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

STYLE_LANG = {"en": "en", "hr": "hi-Latn", "mr": "mr-Latn", "hd": "hi", "md": "mr"}

SLOTS = {
    "en": dict(n=["5", "10", "3", "7"], fmt=["T20", "ODI", "first class"],
               phase=["powerplay", "death overs", "middle overs"],
               tourn=["SMAT", "Ranji Trophy", "Vijay Hazare Trophy", "Syed Mushtaq Ali"],
               dist=["Nagpur", "Amravati", "Akola", "Wardha"],
               grp=["U19", "U16 female", "women", "senior male"],
               bt=["leg-spin", "off-spin", "left-arm orthodox", "pace"],
               pos=["top order", "middle order", "opening"], thr=["20", "25", "30"], thr2=["6", "7", "8"]),
    "hr": dict(n=["5", "10", "3", "7"], fmt=["T20", "ODI", "first class"],
               phase=["powerplay", "death over", "middle over"],
               tourn=["SMAT", "Ranji", "Vijay Hazare", "Mushtaq Ali"],
               dist=["Nagpur", "Amravati", "Akola", "Wardha"],
               grp=["U19", "mahila", "U16 ladkiyon ke", "senior"],
               bt=["leg spin", "off spin", "tez", "spinner"],
               pos=["top order", "middle order", "opener"], thr=["20", "25", "30"], thr2=["6", "7", "8"]),
    "mr": dict(n=["5", "10", "3", "7"], fmt=["T20", "ODI", "first class"],
               phase=["powerplay", "death over", "middle over"],
               tourn=["SMAT", "Ranji", "Vijay Hazare", "Mushtaq Ali"],
               dist=["Nagpur", "Amravati", "Akola", "Wardha"],
               grp=["U19", "mahila", "U16 muli", "senior"],
               bt=["leg spin", "off spin", "vegvan", "phirki"],
               pos=["top order", "middle order", "salami"], thr=["20", "25", "30"], thr2=["6", "7", "8"]),
    "hd": dict(n=["5", "10", "3", "7"], fmt=["T20", "वनडे", "फर्स्ट क्लास"],
               phase=["पावरप्ले", "डेथ ओवर", "मिडल ओवर"],
               tourn=["रणजी", "विजय हजारे", "सय्यद मुश्ताक अली"],
               dist=["नागपुर", "अमरावती", "अकोला", "वर्धा"],
               grp=["अंडर 19", "महिला", "अंडर 16 लड़कियों के", "सीनियर"],
               bt=["लेग स्पिन", "ऑफ स्पिन", "तेज", "स्पिनर"],
               pos=["टॉप ऑर्डर", "मिडल ऑर्डर", "ओपनर"], thr=["20", "25", "30"], thr2=["6", "7", "8"]),
    "md": dict(n=["5", "10", "3", "7"], fmt=["T20", "एकदिवसीय", "फर्स्ट क्लास"],
               phase=["पॉवरप्ले", "डेथ ओव्हर", "मिडल ओव्हर"],
               tourn=["रणजी", "विजय हजारे", "सय्यद मुश्ताक अली"],
               dist=["नागपूर", "अमरावती", "अकोला", "वर्धा"],
               grp=["१९ वर्षांखालील", "महिला", "16 वर्षांखालील मुली", "सीनियर"],
               bt=["लेग स्पिन", "ऑफ स्पिन", "वेगवान", "फिरकी"],
               pos=["टॉप ऑर्डर", "मधली फळी", "सलामी"], thr=["20", "25", "30"], thr2=["6", "7", "8"]),
}

T = {  # intent -> style -> templates
 "batting": {
  "en": ["top {n} {fmt} batters by strike rate", "who scored the most runs in {tourn}",
         "best {grp} batters in the {phase}", "highest run scorers from {dist}",
         "{fmt} batters with boundary percentage over {thr}", "most sixes in {tourn}",
         "{pos} batters with the best strike rate in {fmt}"],
  "hr": ["{fmt} mein strike rate ke hisab se top {n} ballebaaz", "{tourn} mein sabse zyada run kisne banaye",
         "{phase} mein sabse acche ballebaaz dikhao", "{dist} ke sabse zyada run banane wale ballebaaz",
         "{fmt} me boundary percentage {thr} se zyada wale ballebaaz batao",
         "{tourn} mein sabse zyada chhakke kisne lagaye", "{pos} ballebaaz jinka strike rate sabse acha ho"],
  "mr": ["{fmt} madhe strike rate nusar top {n} falandaj", "{tourn} madhe sarvat jast dhava konni kelya",
         "{phase} madhe sarvottam falandaj dakhva", "{dist} che sarvat jast dhava kelele falandaj",
         "{fmt} madhe boundary percentage {thr} peksha jast asleale falandaj sanga",
         "{tourn} madhe sarvat jast shatkar konni marle", "{pos} falandaj jyancha strike rate sarvottam aahe"],
  "hd": ["{fmt} में स्ट्राइक रेट के हिसाब से टॉप {n} बल्लेबाज़", "{tourn} में सबसे ज़्यादा रन किसने बनाए",
         "{phase} में सबसे अच्छे बल्लेबाज़ दिखाओ", "{dist} के सबसे ज़्यादा रन बनाने वाले बल्लेबाज़",
         "{fmt} में बाउंड्री प्रतिशत {thr} से ज़्यादा वाले बल्लेबाज़ बताओ",
         "{tourn} में सबसे ज़्यादा छक्के किसने लगाए"],
  "md": ["{fmt} मध्ये स्ट्राइक रेटनुसार टॉप {n} फलंदाज", "{tourn} मध्ये सर्वात जास्त धावा कोणी केल्या",
         "{phase} मध्ये सर्वोत्तम फलंदाज दाखवा", "{dist} चे सर्वात जास्त धावा करणारे फलंदाज",
         "{fmt} मध्ये बाउंड्री टक्केवारी {thr} पेक्षा जास्त असलेले फलंदाज सांगा",
         "{tourn} मध्ये सर्वाधिक षटकार कोणी मारले"],
 },
 "bowling": {
  "en": ["which bowlers have the best economy in the {phase}", "top {n} {bt} bowlers by wickets in {tourn}",
         "{grp} bowlers with economy under {thr2}", "best {fmt} bowlers by dot ball percentage",
         "most wickets taken in {tourn}"],
  "hr": ["{phase} mein sabse acchi economy wale gendbaaz dikhao",
         "{tourn} mein sabse zyada wicket lene wale top {n} gendbaaz",
         "{grp} gendbaaz jinki economy {thr2} se kam ho", "{fmt} mein dot ball percentage ke hisab se sabse acche gendbaaz",
         "{bt} gendbaaz kaun hain jinhone sabse zyada wicket liye"],
  "mr": ["{phase} madhe sarvottam economy asleale golandaj dakhva",
         "{tourn} madhe sarvat jast bali ghenare top {n} golandaj",
         "{grp} golandaj jyanchi economy {thr2} peksha kami aahe", "{fmt} madhe dot ball percentage nusar sarvottam golandaj",
         "{bt} golandajanpaiki konni sarvat jast bali ghetle"],
  "hd": ["{phase} में सबसे अच्छी इकॉनमी वाले गेंदबाज़ दिखाओ", "{tourn} में सबसे ज़्यादा विकेट लेने वाले टॉप {n} गेंदबाज़",
         "{grp} गेंदबाज़ जिनकी इकॉनमी {thr2} से कम हो", "{fmt} में डॉट बॉल के हिसाब से सबसे अच्छे गेंदबाज़"],
  "md": ["{phase} मध्ये सर्वोत्तम इकॉनॉमी असलेले गोलंदाज दाखवा", "{tourn} मध्ये सर्वात जास्त बळी घेणारे टॉप {n} गोलंदाज",
         "{grp} गोलंदाज ज्यांची इकॉनॉमी {thr2} पेक्षा कमी आहे", "{fmt} मध्ये डॉट बॉल नुसार सर्वोत्तम गोलंदाज"],
 },
 "fielding": {
  "en": ["who took the most catches this season", "best fielders in {tourn}", "top {n} wicket-keepers by stumpings",
         "most run outs by {grp} players", "catches taken per district in {tourn}"],
  "hr": ["is season sabse zyada catch kisne pakde", "{tourn} ke sabse acche fielder dikhao",
         "stumping ke hisab se top {n} wicketkeeper", "{grp} khiladiyon mein sabse zyada run out kisne kiye",
         "{dist} mein sabse zyada catch"],
  "mr": ["ya hangamat sarvat jast zel konni ghetle", "{tourn} madhil sarvottam kshetrarakshak dakhva",
         "stumping nusar top {n} yashtirakshak", "{grp} khelaadunmadhe sarvat jast run out konni kele",
         "{dist} madhe sarvat jast zel"],
  "hd": ["इस सीज़न में सबसे ज़्यादा कैच किसने लिए", "{tourn} के सबसे अच्छे फील्डर दिखाओ",
         "स्टंपिंग के हिसाब से टॉप {n} विकेटकीपर", "सबसे ज़्यादा रन आउट किसने किए"],
  "md": ["या हंगामात सर्वात जास्त झेल कोणी घेतले", "{tourn} मधील सर्वोत्तम क्षेत्ररक्षक दाखवा",
         "स्टंपिंगनुसार टॉप {n} यष्टिरक्षक", "सर्वात जास्त धावचीत कोणी केले"],
 },
 "discipline": {
  "en": ["bowlers with the most wides in {phase}", "which teams give the most no balls",
         "most indisciplined bowlers in {fmt}", "bowlers with most extras in {tourn}"],
  "hr": ["{phase} mein sabse zyada wide dalne wale gendbaaz", "kaun si team sabse zyada no ball deti hai",
         "{fmt} mein sabse zyada extras dene wale gendbaaz batao", "sabse anushasanheen gendbaaz kaun hain"],
  "mr": ["{phase} madhe sarvat jast wide ball takanare golandaj", "konta sangh sarvat jast no ball takto",
         "{fmt} madhe sarvat jast extras denare golandaj sanga", "sarvat beshist golandaj kon aahet"],
  "hd": ["{phase} में सबसे ज़्यादा वाइड डालने वाले गेंदबाज़", "कौन सी टीम सबसे ज़्यादा नो बॉल डालती है",
         "{fmt} में सबसे ज़्यादा एक्स्ट्रा देने वाले गेंदबाज़ बताओ"],
  "md": ["{phase} मध्ये सर्वात जास्त वाइड बॉल टाकणारे गोलंदाज", "कोणता संघ सर्वात जास्त नो बॉल टाकतो",
         "{fmt} मध्ये सर्वाधिक एक्स्ट्रा देणारे गोलंदाज सांगा"],
 },
 "allrounder": {
  "en": ["best all-rounders in {fmt}", "top {n} all-rounders by runs and wickets",
         "which all-rounders are best in {tourn}", "{grp} all-rounders with strike rate above 130"],
  "hr": ["{fmt} ke sabse acche allrounder dikhao", "run aur wicket ke hisab se top {n} allrounder",
         "{tourn} mein sabse behtar allrounder kaun hai"],
  "mr": ["{fmt} madhil sarvottam ashtapailu khelaadu dakhva", "dhava ani bali nusar top {n} ashtapailu",
         "{tourn} madhe sarvottam ashtapailu kon aahe"],
  "hd": ["{fmt} के सबसे अच्छे ऑलराउंडर दिखाओ", "रन और विकेट के हिसाब से टॉप {n} ऑलराउंडर",
         "{tourn} में सबसे बेहतर ऑलराउंडर कौन है"],
  "md": ["{fmt} मधील सर्वोत्तम अष्टपैलू खेळाडू दाखवा", "धावा आणि बळी नुसार टॉप {n} अष्टपैलू",
         "{tourn} मध्ये सर्वोत्तम अष्टपैलू कोण आहे"],
 },
 "general": {
  "en": ["which districts produce the most players", "how many matches were played in {tourn}",
         "which teams won the most matches", "compare districts by total runs"],
  "hr": ["kis zile se sabse zyada khiladi aate hain", "{tourn} mein kitne match khele gaye",
         "kaun si team ne sabse zyada match jeete", "zile ke hisab se kul run dikhao"],
  "mr": ["konatya jilhyatun sarvat jast khelaadu yetat", "{tourn} madhe kiti samane khelle gele",
         "konatya sanghane sarvat jast samane jinkle", "jilhyanusar ekun dhava dakhva"],
  "hd": ["किस जिले से सबसे ज़्यादा खिलाड़ी आते हैं", "{tourn} में कितने मैच खेले गए",
         "किस टीम ने सबसे ज़्यादा मैच जीते", "जिले के हिसाब से कुल रन दिखाओ"],
  "md": ["कोणत्या जिल्ह्यातून सर्वात जास्त खेळाडू येतात", "{tourn} मध्ये किती सामने खेळले गेले",
         "कोणत्या संघाने सर्वात जास्त सामने जिंकले", "जिल्ह्यानुसार एकूण धावा दाखवा"],
 },
}

FIXED = {  # intents with a fixed phrase list per style
 "greeting": {
  "en": ["hi", "hello", "hey there", "help", "good morning", "hello how are you"],
  "hr": ["namaste", "namaste kaise ho", "hello bhai", "madad karo", "namaskar", "hi kaise ho"],
  "mr": ["namaskar", "namaste kasa ahes", "kay challay", "madat kara", "hello kasa aahes", "namaskar mitra"],
  "hd": ["नमस्ते", "नमस्ते कैसे हो", "हेलो", "मदद करो", "नमस्कार"],
  "md": ["नमस्कार", "नमस्कार कसे आहात", "हॅलो", "मदत करा", "कसा आहेस"],
 },
 "out_of_scope": {
  "en": ["what is the weather today", "tell me a joke", "share market news today", "recipe for pasta",
         "best movies to watch", "who will win the election", "book a flight to delhi", "sing a song",
         "write a poem about rain", "what is the capital of france", "how to learn python", "translate this sentence"],
  "hr": ["aaj mausam kaisa hai", "koi joke sunao", "share bazaar ki khabar batao", "paneer ki recipe batao",
         "koi achhi movie batao", "gaana sunao", "chunav ke nateeje kya hain", "delhi ki flight book karo",
         "france ki rajdhani kya hai", "python kaise seekhe"],
  "mr": ["aaj havaman kase aahe", "ek joke sanga", "share bajarachi batmi sanga", "puranpolichi recipe sang",
         "ek changla chitrapat sanga", "gane aikva", "nivadnukiche nikal kay aahet", "dilli sathi flight book kara",
         "francechi rajdhani konti aahe", "python kase shikave"],
  "hd": ["आज मौसम कैसा है", "कोई जोक सुनाओ", "शेयर बाजार की खबर बताओ", "पनीर की रेसिपी बताओ",
         "कोई अच्छी फिल्म बताओ", "गाना सुनाओ", "चुनाव के नतीजे क्या हैं", "फ्रांस की राजधानी क्या है", "पायथन कैसे सीखें"],
  "md": ["आज हवामान कसे आहे", "एक जोक सांगा", "शेअर बाजाराची बातमी सांगा", "पुरणपोळीची रेसिपी सांग",
         "एखादा चांगला चित्रपट सांगा", "गाणे ऐकव", "निवडणुकीचे निकाल काय आहेत", "फ्रान्सची राजधानी कोणती आहे",
         "पायथन कसे शिकावे"],
 },
 "external_data": {
  "en": ["who scored the most runs in IPL", "virat kohli strike rate", "world cup top bowlers",
         "india international team stats", "ms dhoni stumpings", "test match best batters"],
  "hr": ["IPL mein sabse zyada run kisne banaye", "virat kohli ka strike rate batao", "world cup ke top gendbaaz",
         "international cricket mein sabse zyada wicket", "dhoni ke stumping"],
  "mr": ["IPL madhe sarvat jast dhava konni kelya", "virat kohli cha strike rate sanga",
         "vishwachashakatil top golandaj", "antararashtriya cricket madhe sarvat jast bali", "dhoni che stumping"],
  "hd": ["IPL में सबसे ज़्यादा रन किसने बनाए", "विराट कोहली का स्ट्राइक रेट बताओ", "वर्ल्ड कप के टॉप गेंदबाज़",
         "अंतरराष्ट्रीय क्रिकेट में सबसे ज़्यादा विकेट", "धोनी के स्टंपिंग"],
  "md": ["IPL मध्ये सर्वात जास्त धावा कोणी केल्या", "विराट कोहलीचा स्ट्राइक रेट सांगा", "विश्वचषकातील टॉप गोलंदाज",
         "आंतरराष्ट्रीय क्रिकेटमध्ये सर्वाधिक बळी", "धोनीचे स्टंपिंग"],
 },
}

_PREFIX = {"en": ["", "please ", "hey ", "can you tell "], "hr": ["", "bhai ", "please ", "zara "],
           "mr": ["", "please ", "mitra ", "ek minute "], "hd": ["", "कृपया ", "भाई "], "md": ["", "कृपया ", "मित्रा "]}


def generate(per_cell: int = 14, seed: int = 7) -> list[tuple[str, str, str]]:
    """Returns [(text, intent, language_code)]."""
    rng = random.Random(seed)
    rows: dict[tuple, None] = {}
    for intent, by_style in T.items():
        for style, templates in by_style.items():
            for _ in range(per_cell * 4):                 # oversample, then de-duplicate
                if sum(1 for r in rows if r[1] == intent and r[2] == STYLE_LANG[style]) >= per_cell:
                    break
                tpl = rng.choice(templates)
                vals = {k: rng.choice(v) for k, v in SLOTS[style].items()}
                text = tpl.format(**vals)
                if rng.random() < 0.15:
                    text = rng.choice(_PREFIX[style]) + text
                rows[(text, intent, STYLE_LANG[style])] = None
    for intent, by_style in FIXED.items():
        for style, phrases in by_style.items():
            for ph in phrases:
                for pre in _PREFIX[style]:
                    rows[(pre + ph, intent, STYLE_LANG[style])] = None
    out = list(rows)
    rng.shuffle(out)
    return out


def write_csv(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["text", "intent", "lang"])
        w.writerows(rows)
