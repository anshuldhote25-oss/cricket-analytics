"""
nlp/lint.py - sanity checks for the lexicon. Run:  python -m nlp.lint

1. Lists forms that share a phonetic key but map to different meanings.
2. Warns when a common Hindi/Marathi/English function word would be mistaken for a
   cricket term (e.g. 'mein' -> 'men').
"""
from . import entities as E
from .lang_id import _EN_STRONG, _EN_WEAK, _HI_DEV_STRONG, _HI_DEV_WEAK, _HI_LAT_STRONG, _HI_LAT_WEAK, \
    _MR_DEV_STRONG, _MR_DEV_WEAK, _MR_LAT_STRONG, _MR_LAT_WEAK
from .lexicon import LEXICON
from .normalize import token_key, tokenize


def main() -> int:
    problems = 0
    print(f"lexicon index: {len(E.INDEX)} phonetic keys, {len(E.RAW_INDEX)} raw-spelling forms")
    for form, a, b in E.COLLISIONS:
        print(f"  COLLISION  {form!r}: {a} vs {b}")
        problems += 1
    all_forms = {t for cat in LEXICON.values() for spec in cat.values() for f in spec["forms"]
                 for t in tokenize(f.lstrip("="))}
    extra_english = ("a an to on at is was were be been player players season match matches list show name get find "
                     "who how much more less than then there their these those our your you i we they it its not no "
                     "yes also only just very each every some such same other another new old young").split()
    extra_indic = ("aap tum hum main yeh woh kuch bhi sab sirf abhi par tak toh mera tera kahan kab kyun ho hoga tha thi "
                   "raha rahi karo kare karna lena dena aana jana bhai yaar dost tumhi aamhi majhe tuzhe he nahi kay kuthe "
                   "kasa kadhi ka tar pan aani mhanje ahe aur hain kaise kitna "
                   "आप तुम हम यह वह कुछ भी सब सिर्फ अब पर तक तो मेरा कहां कब क्यों हो होगा था थी करो करना भाई यार "
                   "तुम्ही आम्ही माझे तुझे हे नाही काय कुठे कसा केव्हा का तर पण म्हणजे आहे").split()
    words = (extra_indic + extra_english + _EN_STRONG + _HI_DEV_STRONG + _HI_DEV_WEAK + _MR_DEV_STRONG + _MR_DEV_WEAK +
             _HI_LAT_STRONG + _HI_LAT_WEAK + _MR_LAT_STRONG + _MR_LAT_WEAK)
    for w in sorted(set(words)):
        if w in all_forms:        # deliberate dual-use word (e.g. 'golandaj' is both a marker and a cricket term)
            continue
        hit = E.INDEX.get((token_key(w),)) or E.RAW_INDEX.get((w,))
        if hit:
            print(f"  FUNCTION WORD {w!r} would be read as {hit[0]}={hit[1]}")
            problems += 1
    print("ok - no problems" if not problems else f"{problems} problem(s)")
    return problems


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
