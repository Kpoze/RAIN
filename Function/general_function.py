import re
import os
import json
from dotenv import load_dotenv
import ast
import re
from langdetect import detect
import deep_translator 
from googletrans import Translator as GoogleTransTranslator
import time
load_dotenv()

def is_open_source(license_info):
    allowed = {
        "agpl-3.0",      
        "apache-2.0",    
        "bsd-2-clause",  
        "bsd-3-clause",  
        "cc0-1.0",      
        "epl-2.0",       
        "gpl-2.0",      
        "gpl-3.0",       
        "lgpl-2.1",     
        "lgpl-3.0",     
        "mit",           
        "mpl-2.0",      
        "unlicense"      
    }

    if license_info is None or license_info == "":
        return True  # Considéré comme valide

    elif isinstance(license_info, dict):
        key = license_info.get("key")
        if not key:
            return True  # Si key est vide ou None, on garde
        return key.lower() in allowed

    elif isinstance(license_info, str):
        license_text = license_info.lower()
        return license_text in allowed or license_text == ""

    return False



def parse_count(text):
    numb        = text.lower().replace(",", "").strip()
    match       = re.search(r"[\d\.]+[kKmM]?", numb)
    if not match:
        return 0
    else : 
        numb       = match.group(0) 
        if "k" in numb:
            return int(float(numb.replace("k", "")) * 1000)
        elif "m" in numb:
            return int(float(numb.replace("m", "")) * 1_000_000)
        return int(numb) if numb.isdigit() else 0
    


def safe_eval(x):
    if isinstance(x, str):
        try:
            return ast.literal_eval(x)
        except Exception:
            try:
                return json.loads(x)
            except Exception:
                return {}
    return x if isinstance(x, dict) else {}



def safe_parse_topics(val):
    # Si c'est déjà une vraie liste, on la garde
    if isinstance(val, list):
        return val
    # Si c'est une chaîne, essayer d'abord de parser proprement
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
        # Sinon, nettoyer le format corrompu
        return re.findall(r'[a-zA-Z0-9\-]+', val)
    return []



ASIAN_LANGUAGES = {'lt','pl','lt','tl','cy','et','so','fi','pt','sl','ro','zh-cn', 'zh-tw', 'ja', 'ko', 'th', 'vi', 'km', 'lo', 'my', 'bn', 'hi', 'ta', 'te', 'ml', 'mr', 'gu', 'pa', 'si','no','nl','ca','id','af','fr'}

def detect_the_lang(text):
    try:
        lang = detect(text)
        #print(lang)
        return lang
    except Exception as e:
        print(f"[detect_the_lang] Erreur : {e}")
        return "en"  # fallback vers l'anglais

def translate_multilang(text, idx=None, max_retries=3, delay=1.0):
    if not isinstance(text, str) or not text.strip():
        return "",""
    attempts = 0
    while attempts < max_retries:
        try:
            lang = detect_the_lang(text)
            if lang == 'en':
                translated = text # Pas besoin de traduire
                return translated,lang
            elif lang in ASIAN_LANGUAGES or lang.startswith(tuple(ASIAN_LANGUAGES)):  # chinois (simplifié ou traditionnel)
                try:
                    translator = GoogleTransTranslator()
                    translated = translator.translate(text, src='auto', dest='en').text
                    if translated.strip().lower() == "into":
                        translated = ""
                    return translated,lang
                    print(f"[googletrans] Ligne {idx if idx is not None else '?'} traduite : {translated}")
                except Exception as e:
                    print(f"[Erreur googletrans] {e}")
                    translated = text
                    return translated,lang
            else:
                # Étape 1 : langue détectée → français
                translated = deep_translator.GoogleTranslator(source=lang, target='en').translate(text)

                print(f"[OK] Ligne {idx if idx is not None else '?'} traduite_en : {translated}")
                return translated,lang
        except Exception as e:
            print(f"[ERROR] Ligne {idx if idx is not None else '?'} : {e}")
            attempts += 1
            time.sleep(delay)

