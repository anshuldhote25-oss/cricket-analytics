"""
nlp/lexicon.py - multilingual cricket gazetteer (the NER dictionary).

Every entry maps many surface forms - English, Hindi, Marathi, in Devanagari AND in
Roman letters - to ONE canonical value that the database understands.

    LEXICON[category][canonical] = {"sql": <hint for the LLM>, "forms": [surface forms]}

Forms are matched through phonetic keys (see normalize.py), so you do not have to list
every spelling: 'gendbaaz', 'gendbaj' and 'गेंदबाज़' are already the same key. Only list
forms that sound genuinely different (e.g. 'wide' vs 'वाइड', 'catch' vs 'कैच').

To teach the system a new word, add it to the right 'forms' string below and run
    python -m nlp.evaluate
"""
from __future__ import annotations


def _e(sql, forms: str) -> dict:
    return {"sql": sql, "forms": [f.strip() for f in forms.split("|") if f.strip()]}


LEXICON: dict[str, dict[str, dict]] = {

    # ------------------------------------------------------------------ format
    "format": {
        "T20": _e("format = 'T20'",
                  "t20|t 20|twenty20|twenty 20|twenty twenty|t twenty|ti twenty|ti 20|"
                  "टी20|टी 20|टी-20|टी ट्वेंटी|टी ट्वेन्टी|टी ट्वेंटी|20-20"),
        "ODI": _e("format = 'ODI'",
                  "odi|odis|one day|oneday|50 over|50 overs|50 ओवर|50 ओव्हर|50 ओवर्स|"
                  "वनडे|वन डे|एकदिवसीय|एक दिवसीय|ekdivasiya|ek divasiya|ekdivasiy|ek divsiya|"
                  "vanday|van day|एकदिवसीय सामने|fifty over"),
        "FirstClass": _e("format = 'FirstClass'",
                         "first class|firstclass|=fc|फर्स्ट क्लास|फर्स्टक्लास|farst klas|first klas|"
                         "multi day|multiday|मल्टी डे"),
    },

    # -------------------------------------------------------------- tournament
    "tournament": {
        "SMAT": _e("tournament_name LIKE '%Mushtaq%'",
                   "smat|syed mushtaq ali|mushtaq ali|mushtaq|सय्यद मुश्ताक अली|सैयद मुश्ताक अली|"
                   "मुश्ताक अली|मुश्ताक|sayyad mushtaq ali|sayed mushtaq ali|mushtak ali|mushtak"),
        "VHT": _e("tournament_name LIKE '%Hazare%'",
                  "=vht|vijay hazare|hazare|विजय हजारे|हजारे|vijay hajare|hajare"),
        "Ranji": _e("tournament_name LIKE '%Ranji%'",
                    "ranji|रणजी|ranaji|ranjee|ranji trophy|रणजी ट्रॉफी"),
        "CK Nayudu": _e("tournament_name LIKE '%Nayudu%'",
                        "nayudu|ck nayudu|c k nayudu|col ck nayudu|नायडू|सी के नायडू|naidu"),
        "Vinoo Mankad": _e("tournament_name LIKE '%Mankad%'",
                           "mankad|vinoo mankad|विनू मांकड|मांकड|विनू मंकड|मंकड"),
        "Vijay Merchant": _e("tournament_name LIKE '%Merchant%'",
                             "merchant|vijay merchant|विजय मर्चंट|मर्चंट"),
    },

    # ------------------------------------------------------------------ gender
    "gender": {
        "female": _e("gender = 'female'",
                     "female|females|women|womens|woman|girls|girl|ladies|lady|"
                     "महिला|महिलाओं|महिलांचे|महिलांच्या|मुली|मुलींच्या|मुलींचे|लड़की|लड़कियों|लड़कियां|"
                     "वुमन|वुमेन|mahila|mahilaon|mahilanche|mahilanchya|ladki|ladkiyon|ladkiya|"
                     "muli|mulinchya|mulinche|stri|vuman"),
        "male": _e("gender = 'male'",
                   "male|males|=men|=mens|boys|boy|gents|पुरुष|पुरुषों|पुरुषांचे|पुरुषांच्या|"
                   "लड़के|लड़कों|मुले|मुलांचे|मुलांच्या|purush|purushon|purushanche|"
                   "ladke|ladkon|mule|mulanche|mulanchya"),
    },

    # --------------------------------------------------------------- age group
    "age_group": {
        "U19": _e("age_group = 'U19'",
                  "u 19|under 19|under nineteen|अंडर 19|अंडर-19|andar 19|"
                  "19 varshakhalil|19 varshankhalil|19 वर्षांखालील|19 वर्षाखालील|19 साल से कम|19 saal se kam"),
        "U16": _e("age_group = 'U16'",
                  "u 16|under 16|under sixteen|अंडर 16|अंडर-16|andar 16|"
                  "16 varshakhalil|16 varshankhalil|16 वर्षांखालील|16 वर्षाखालील|16 साल से कम|16 saal se kam"),
        "U25": _e("age_group = 'U25'",
                  "u 25|under 25|अंडर 25|अंडर-25|andar 25|25 varshakhalil|25 वर्षांखालील|25 साल से कम"),
        "senior": _e("age_group = 'senior'",
                     "senior|seniors|सीनियर|siniyar|seniyar|वरिष्ठ|varishth|varishtha"),
    },

    # ------------------------------------------------------------ bowler type
    "bowler_type": {
        "right-arm pace": _e("bowler_type = 'right-arm pace'",
                             "right arm pace|right arm fast|right arm pacer|right arm tez|right arm vegvan|"
                             "राइट आर्म तेज|राइट आर्म वेगवान|राइट आर्म पेस"),
        "left-arm pace": _e("bowler_type = 'left-arm pace'",
                            "left arm pace|left arm fast|left arm pacer|left arm seam|left arm tez|"
                            "left arm vegvan|लेफ्ट आर्म तेज|लेफ्ट आर्म वेगवान|लेफ्ट आर्म पेस|"
                            "डावखुरा वेगवान|डावखुरे वेगवान|dawkhura vegvan|davkhura vegvan|baen hath ka tez"),
        "right-arm medium pace": _e("bowler_type = 'right-arm medium pace'",
                                    "medium pace|medium pacer|medium pacers|medium fast|medium|"
                                    "मीडियम पेस|मीडियम पेसर|मध्यम गती|मध्यम गतीचे|मध्यम तेज|"
                                    "madhyam gati|madhyam gatiche|madhyam tez|medium tez"),
        "pace": _e("bowler_type IN ('right-arm pace','left-arm pace','right-arm medium pace')",
                   "pace|pacer|pacers|fast|seam|seamer|seamers|speedster|"
                   "तेज|पेसर|पेस|वेगवान|tez|vegvan|vegwan|pesar"),
        "leg-spin": _e("bowler_type = 'leg-spin'",
                       "leg spin|legspin|leg spinner|leg spinners|leg break|"
                       "लेग स्पिन|लेगस्पिन|लेग स्पिनर|लेग ब्रेक|leg spinar|leg spiner"),
        "off-spin": _e("bowler_type = 'off-spin'",
                       "off spin|offspin|off spinner|off spinners|off break|"
                       "ऑफ स्पिन|ऑफस्पिन|ऑफ स्पिनर|ऑफ ब्रेक|off spinar"),
        "left-arm orthodox": _e("bowler_type = 'left-arm orthodox'",
                                "left arm orthodox|orthodox|left arm spin|left arm spinner|slow left arm|=sla|"
                                "लेफ्ट आर्म ऑर्थोडॉक्स|ऑर्थोडॉक्स|लेफ्ट आर्म स्पिन|लेफ्ट आर्म स्पिनर|"
                                "डावखुरा स्पिनर|डावखुरे फिरकीपटू|डावखुरा फिरकी|dawkhura spinner|davkhura spinner|"
                                "dawkhura phirki|left arm spinar"),
        "left-arm wrist spin": _e("bowler_type = 'left-arm wrist spin'",
                                  "wrist spin|wrist spinner|chinaman|left arm wrist spin|"
                                  "रिस्ट स्पिन|रिस्ट स्पिनर|चायनामन|wrist spinar"),
        "spin": _e("bowler_type IN ('off-spin','leg-spin','left-arm orthodox','left-arm wrist spin')",
                   "spin|spinner|spinners|स्पिन|स्पिनर|स्पिनरों|"
                   "फिरकी|फिरकीपटू|firki|phirki|phirkipatu|spinar|spiner"),
    },

    # -------------------------------------------------------------------- role
    # (no SQL for plain batter/bowler: those words choose the *view*, not a filter)
    "role": {
        "batter": _e(None,
                     "batter|batters|batsman|batsmen|batting|hitter|hitters|"
                     "बल्लेबाज|बल्लेबाजों|बल्लेबाजी|बैट्समन|बैट्समैन|बैटर|बैटर्स|बैटिंग|"
                     "फलंदाज|फलंदाजांमध्ये|फलंदाजी|फलंदाजांचे|फलंदाजांच्या|"
                     "ballebaaz|ballebaj|ballebaz|balleybaaz|baleybaz|ballebaazi|ballebazi|"
                     "falandaj|falandaaz|falandaz|phalandaj|falandaji|phalandazi|falandajanchya|baitar|batsmaan"),
        "bowler": _e(None,
                     "bowler|bowlers|bowling|bowlar|bowlars|"
                     "गेंदबाज|गेंदबाजों|गेंदबाजी|बॉलर|बॉलर्स|बोलर|बॉलिंग|"
                     "गोलंदाज|गोलंदाजांमध्ये|गोलंदाजी|गोलंदाजांचे|गोलंदाजांच्या|"
                     "gendbaaz|gendbaj|gendbaz|gaindbaaz|gendbaazi|gendbazi|"
                     "golandaj|golandaaz|golandaz|golandaji|golandajanchya|bolar|bolars"),
        "all-rounder": _e("player_role = 'all-rounder'",
                          "all rounder|all-rounder|allrounder|all rounders|allrounders|all round|"
                          "ऑलराउंडर|ऑल राउंडर|ऑलराउंडरों|अष्टपैलू|अष्टपैलू खेळाडू|हरफनमौला|हरफन मौला|"
                          "ashtapailu|ashtpailu|ashtapailoo|ashtapaylu|harfanmaula|harfan maula|"
                          "olrounder|olraundar|all raundar"),
        "wicket-keeper": _e("player_role = 'wicket-keeper'",
                            "wicket keeper|wicketkeeper|wicketkeepers|wicket keepers|keeper|keepers|=wk|"
                            "विकेटकीपर|विकेट कीपर|विकेटकीपरों|विकेटकीपर्स|यष्टिरक्षक|यष्टीरक्षक|"
                            "yashtirakshak|yashtirakshakanchya|wicketkipar|wicket kipar"),
        "fielder": _e(None,
                      "fielder|fielders|fielding|feilder|फील्डर|फील्डिंग|फील्डरों|"
                      "क्षेत्ररक्षक|क्षेत्ररक्षण|क्षेत्ररक्षकांमध्ये|क्षेत्ररक्षकांचे|"
                      "kshetrarakshak|kshetrarakshan|kshetrarakshakanchya|fildar|filding"),
    },

    # ------------------------------------------------------------------ metric
    "metric": {
        "strike_rate": _e("strike_rate",
                          "strike rate|strikerate|=sr|स्ट्राइक रेट|स्ट्राईक रेट|स्ट्राइकरेट|स्ट्राईकरेट|"
                          "straik rate|strike rat|strike|स्ट्राइक"),
        "economy_rate": _e("economy_rate",
                           "economy|economy rate|=eco|इकॉनमी|इकॉनॉमी|इकोनॉमी|इकोनोमी|इकॉनमी रेट|इकॉनॉमी रेट|"
                           "इकोनॉमी रेट|ikonomi|economi|ekonomy|ikonomy|ekonomi"),
        "runs": _e("total_runs",
                   "runs|run|runs scored|total runs|रन|रन्स|रनों|कुल रन|"
                   "धावा|धावांचे|धावांच्या|एकूण धावा|धावसंख्या|धाव|"
                   "dhava|dhaava|dhawa|dhave|dhavanche|ekun dhava|dhav"),
        "wickets": _e("wickets",
                      "wickets|wicket|wkts|विकेट|विकेट्स|विकेटें|विकेटों|बळी|बळींची|"
                      "bali|balee|baali|vicket|vickets|wiket|wikets"),
        "catches": _e("catches",
                      "catches|catch|catches taken|कैच|कैचेस|कॅच|कॅचेस|झेल|झेलांची|"
                      "jhel|jhele|zel|zele|kaich|cach|kaitch"),
        "stumpings": _e("stumpings",
                        "stumping|stumpings|stumped|स्टंपिंग|स्टंप|यष्टिचीत|यष्टीचीत|"
                        "yashtichit|stamping"),
        "run_outs": _e("run_outs",
                       "run out|run outs|runout|runouts|रन आउट|रनआउट|रन आउट्स|रन आऊट|धावचीत|"
                       "dhavchit|dhawchit|dhavachit|run aut|runaut"),
        "wides": _e("wides",
                    "wide|wides|wide ball|wide balls|वाइड|वाईड|वाइड बॉल|वाईड बॉल|वाईड बॉल्स|वाइड बॉल्स|"
                    "vaid|vaaid|vide|wid"),
        "no_balls": _e("noballs",
                       "no ball|no balls|noball|noballs|नो बॉल|नो बॉल्स|नोबॉल|नो बाल|नो बॉल्स|"
                       "no baal|no bol|nobal"),
        "extras": _e("total_extras_runs",
                     "extras|extra|extra runs|एक्स्ट्रा|एक्स्ट्रा रन|अतिरिक्त|अतिरिक्त रन|अवांतर|अवांतर धावा|"
                     "avantar|avantar dhava|atirikt|atirikt run|ekstra"),
        "dot_balls": _e("dot_ball_percentage",
                        "dot ball|dot balls|dot|dots|डॉट बॉल|डॉट बॉल्स|डॉट|dot baal"),
        "boundary_pct": _e("boundary_percentage",
                           "boundary|boundaries|boundary percentage|बाउंड्री|बाउंड्रीज|बाऊंड्री|"
                           "boundri|baundri|baundari|baundary"),
        "fours": _e("fours",
                    "=four|=fours|चौका|चौके|चौकार|चौक्के|chauka|chauke|chaukar"),
        "sixes": _e("sixes",
                    "six|sixes|sixer|सिक्स|सिक्सेस|छक्का|छक्के|षटकार|षटकारांची|"
                    "chhakka|chhakke|chakka|chakke|shatkar|shatkaar"),
        "average": _e("bowling_average",
                      "average|averages|=avg|एवरेज|ऍव्हरेज|अॅव्हरेज|सरासरी|औसत|"
                      "sarasari|ausat|evrej|avrej"),
        "indiscipline": _e("indiscipline_rate",
                           "indiscipline|undisciplined|indisciplined|discipline|अनुशासनहीन|अनुशासन|बेशिस्त|शिस्त|"
                           "beshist|shist|anushasanheen|anushasan"),
    },

    # ------------------------------------------------------------------- phase
    "phase": {
        "powerplay": _e("phase = 'powerplay'",
                        "powerplay|power play|=pp|पावरप्ले|पावर प्ले|पॉवरप्ले|पॉवर प्ले|पावरप्लै|"
                        "pavarple|pavar ple|povarple|pavarplay|pawar play|powerple|power ple|paverple|"
                        "starting overs|opening overs|shuruaati over|shuruati over|shuruvatichya over|"
                        "shuruvatichya shatkat|शुरुआती ओवर|शुरुआती ओवरों|शुरुवातीच्या षटकांत|"
                        "सुरुवातीच्या षटकांत|सुरुवातीची षटके"),
        "death": _e("phase = 'death'",
                    "death|death overs|death over|डेथ|डेथ ओवर|डेथ ओव्हर|डेथ ओवर्स|डेथ ओव्हर्स|"
                    "det over|det overs|deth over|deth overs|last overs|last over|slog overs|end overs|"
                    "antim over|antim overs|antim shatke|antim shatkat|अंतिम ओवर|अंतिम षटके|अंतिम षटकांत|"
                    "अंतिम ओव्हर|आखिरी ओवर|आखिरी ओवरों|akhri over|akhiri over|aakhri over|akhri overon|"
                    "shevtchya shatkat|शेवटच्या षटकांत|शेवटची षटके|shevtchi shatke|shevtchya over"),
        "middle": _e("phase = 'middle'",
                     "middle|middle overs|middle over|mid overs|मिडल|मिडल ओवर|मिडल ओव्हर|मिडल ओवर्स|मिडल ओव्हर्स|"
                     "midal over|middle phase|मधली षटके|मधल्या षटकांत|मधल्या षटकांमध्ये|मधले ओव्हर|"
                     "madhli shatke|madhlya shatkat|madhle over|madhlya over|"
                     "बीच के ओवर|बीच के ओवरों|beech ke over|beech ke overon"),
    },

    # ---------------------------------------------------------- batting order
    "position": {
        "top_order": _e("batter_position <= 3",
                        "top order|toporder|टॉप ऑर्डर|टॉप-ऑर्डर|toparder|top aardar"),
        "opener": _e("batter_position <= 2",
                     "opener|openers|opening batter|opening batters|opening batsman|opening|"
                     "ओपनर|ओपनिंग|सलामी|सलामीवीर|सलामीचे|salami|salamiveer|opnar"),
        "middle_order": _e("batter_position BETWEEN 4 AND 6",
                           "middle order|मिडल ऑर्डर|मधली फळी|मधल्या फळीतील|मध्यक्रम|मध्यम क्रम|"
                           "madhli fali|madhlya faliti|madhyakram|madhyam kram|midal order"),
        "lower_order": _e("batter_position >= 7",
                          "lower order|=tail|=tailenders|tail enders|tail ender|लोअर ऑर्डर|निचला क्रम|निचले क्रम|"
                          "खालची फळी|खालच्या फळीतील|nichla kram|nichle kram|khalchi fali|khalchya faliti|loar order"),
    },

    # ---------------------------------------------------------------- district
    "district": {
        "Nagpur": _e("district = 'Nagpur'", "nagpur|नागपूर|नागपुर|nagpoor"),
        "Amravati": _e("district = 'Amravati'", "amravati|amaravati|अमरावती|amrawati"),
        "Wardha": _e("district = 'Wardha'", "wardha|vardha|वर्धा"),
        "Yavatmal": _e("district = 'Yavatmal'", "yavatmal|yavatmaal|यवतमाळ|यवतमाल|yeotmal"),
        "Akola": _e("district = 'Akola'", "akola|अकोला"),
        "Buldhana": _e("district = 'Buldhana'", "buldhana|buldana|बुलढाणा|बुलडाणा"),
        "Chandrapur": _e("district = 'Chandrapur'", "chandrapur|chandrapoor|चंद्रपूर|चंद्रपुर|chanderpur"),
        "Gondia": _e("district = 'Gondia'", "gondia|gondiya|गोंदिया|gondya"),
        "Bhandara": _e("district = 'Bhandara'", "bhandara|भंडारा"),
        "Gadchiroli": _e("district = 'Gadchiroli'", "gadchiroli|गडचिरोली|gadchiroly"),
        "Washim": _e("district = 'Washim'", "washim|vashim|वाशिम|vasim"),
    },

    # -------------------------------------------------- "group by" vocabulary
    "group": {
        "district": _e("GROUP BY district",
                       "district|districts|जिला|जिले|जिलों|जिल्हा|जिल्हे|जिल्ह्यातून|जिल्ह्यातील|"
                       "zila|zile|jila|jile|jilha|jilhe|jilhyatun|jilhyatil|zilla|jilhyat"),
        "team": _e("GROUP BY team",
                   "team|teams|टीम|टीमें|=संघ|=sangh|=sanghat|=sangha|tim"),
    },

    # --------------------------------------------- ranking / direction words
    "direction": {
        "top": _e(None,
                  "top|first|टॉप|पहिले|पहले|शीर्ष|pahile|pehle|shirsh|topmost"),
        "desc": _e("ORDER BY ... DESC",
                   "highest|most|=max|maximum|best|greatest|"
                   "sabse zyada|sabse jyada|sabse jada|sabse acche|sabse achhe|sabse accha|sabse achha|"
                   "sabse achi|sabse acchi|sabse badhiya|sabse behtar|sabse behtarin|sab se zyada|sab se acche|"
                   "sarvadhik|sarvottam|sarvashreshth|sarvat jast|sarvat jasta|sarvat changle|sarvat changla|"
                   "sarvat uttam|सबसे ज्यादा|सबसे ज़्यादा|सबसे अच्छे|सबसे अच्छा|सबसे अच्छी|सबसे बढ़िया|"
                   "सबसे बेहतर|सबसे बेहतरीन|सर्वाधिक|सर्वोत्तम|सर्वश्रेष्ठ|सर्वात जास्त|सर्वात चांगले|"
                   "सर्वात चांगला|सर्वात उत्तम|अधिकतम|सबसे अधिक"),
        "asc": _e("ORDER BY ... ASC",
                  "lowest|least|=min|minimum|fewest|worst|bottom|"
                  "sabse kam|sab se kam|sabse kharab|sabse bura|sabse kamjor|"
                  "sarvat kami|sarvat kmi|sarvat kam|sarvat vait|sarvat waait|"
                  "सबसे कम|सबसे खराब|सबसे बुरा|सबसे कमजोर|न्यूनतम|सर्वात कमी|सर्वात वाईट|सर्वात कमकुवत"),
    },

    # ------------------------------------------ comparison words ("under 7" ...)
    # *_pre  : word comes BEFORE the number  (English: "under 7")
    # *_post : word comes AFTER  the number  (Hindi/Marathi: "7 से कम", "7 पेक्षा कमी")
    "cmp": {
        "lt_pre": _e(None, "under|below|less than|lower than|fewer than|lesser than"),
        "gt_pre": _e(None, "over|above|more than|greater than|higher than"),
        "lt_post": _e(None,
                      "se kam|se kami|pexa kami|peksha kami|pexa kam|peksha kam|se neeche|se niche|"
                      "से कम|से कमी|पेक्षा कमी|पेक्षा कम|से नीचे"),
        "gt_post": _e(None,
                      "se zyada|se jyada|se jada|se jast|se adhik|se upar|pexa jast|peksha jast|pexa adhik|"
                      "peksha adhik|pexa jasta|peksha jasta|से ज्यादा|से ज़्यादा|से अधिक|से ऊपर|"
                      "पेक्षा जास्त|पेक्षा अधिक"),
    },

    # ------------------------------------------------------------ out of scope
    "oos": {
        "weather": _e(None, "weather|temperature|rain|mausam|मौसम|havaman|हवामान|pavus|पाऊस|baarish|बारिश"),
        "finance": _e(None,
                      "stock|stocks|share market|stock market|sensex|nifty|finance|शेयर|शेअर|"
                      "share bazaar|share bajar|शेयर बाजार|शेअर बाजार|सेंसेक्स|bazaar|बाजार|bajar"),
        "news_politics": _e(None,
                            "news|khabar|खबर|समाचार|batmi|batami|बातमी|politics|political|राजनीति|राजकारण|"
                            "election|elections|चुनाव|निवडणूक|nivadnuk|chunav|rajniti|rajkaran"),
        "food": _e(None, "recipe|recipes|रेसिपी|पाककृती|khana|खाना|jevan|जेवण"),
        "travel": _e(None, "travel|flight|flights|hotel|trip|yatra|यात्रा|प्रवास|pravas"),
        "entertainment": _e(None,
                            "movie|movies|film|films|cinema|song|songs|poem|gana|gaana|gane|गाना|गाने|गीत|"
                            "फिल्म|सिनेमा|चित्रपट|chitrapat|kavita|कविता|joke|jokes|चुटकुला"),
    },

    # ------------------------------------- data we do not have (not in database)
    "external": {
        "league_intl": _e(None,
                          "ipl|आईपीएल|आयपीएल|आय पी एल|world cup|worldcup|वर्ल्ड कप|वर्ल्डकप|विश्व कप|विश्वचषक|विश्वचषकातील|विश्वचषकात|vishwa cup|vishwachashak|"
                          "vishwachashakat|international|internationals|आंतरराष्ट्रीय|अंतरराष्ट्रीय|"
                          "antararashtriya|antarrashtriya|national team|team india|indian team|भारतीय संघ|"
                          "टीम इंडिया|bharatiya sangh|test match|test cricket|टेस्ट मैच|टेस्ट क्रिकेट|कसोटी|kasoti|"
                          "asia cup|एशिया कप|bbl|psl"),
        "celebrity": _e(None,
                        "kohli|कोहली|dhoni|धोनी|tendulkar|तेंडुलकर|तेंदुलकर|bumrah|बुमराह|virat|विराट|"
                        "rohit sharma|रोहित शर्मा"),
    },

    # ----------------------------------------------------------------- greeting
    "greeting": {
        "hello": _e(None,
                    "=hi|=hello|=hey|namaste|namaskar|नमस्ते|नमस्कार|kaise ho|kasa ahes|kay challay|kasa aahes|"
                    "कैसे हो|कसा आहेस|कसे आहात|help|madad|मदद|madat|मदत|good morning|good evening|"
                    "शुभ प्रभात|शुभ सकाळ"),
    },
}

# Categories that count as "this question is about our cricket data".
DOMAIN_CATEGORIES = {"format", "tournament", "gender", "age_group", "bowler_type", "role",
                     "metric", "phase", "position", "district", "group", "player"}

# Human readable labels used for the English "interpreted as" line.
LABELS = {
    "strike_rate": "strike rate", "economy_rate": "economy rate", "runs": "runs",
    "wickets": "wickets", "catches": "catches", "stumpings": "stumpings", "run_outs": "run outs",
    "wides": "wides", "no_balls": "no balls", "extras": "extras", "dot_balls": "dot ball %",
    "boundary_pct": "boundary %", "fours": "fours", "sixes": "sixes", "average": "average",
    "indiscipline": "indiscipline (wides + no balls)",
    "top_order": "top-order", "opener": "opening", "middle_order": "middle-order",
    "lower_order": "lower-order",
}
