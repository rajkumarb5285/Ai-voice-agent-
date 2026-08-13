"""
Bhojpuri Text Normalization Engine
Converts currency, numbers, time, dates, percentages, symbols, and technical terms
into natural spoken Bhojpuri form before TTS synthesis.
"""
import re
from typing import Dict

class BhojpuriNormalizer:
    """Normalizes numbers, currency, time, dates, and symbols into spoken Bhojpuri."""

    BHOJPURI_DIGITS = {
        '0': 'शून्य', '1': 'एक', '2': 'दू', '3': 'तीन', '4': 'चार',
        '5': 'पांच', '6': 'छह', '7': 'सात', '8': 'आठ', '9': 'नौ', '10': 'दस',
        '11': 'ग्यारह', '12': 'बारह', '15': 'पंद्रह', '20': 'बीस', '25': 'पच्चीस',
        '30': 'तीस', '40': 'चालिस', '50': 'पचास', '60': 'साठ', '70': 'सत्तर',
        '80': 'अस्सी', '90': 'नब्बे', '100': 'सौ', '1000': 'हजार', '100000': 'लाख',
        '10000000': 'करोड़'
    }

    def __init__(self):
        pass

    def _num_to_bhojpuri(self, num_str: str) -> str:
        """Convert an integer string into spoken Bhojpuri text."""
        try:
            num = int(num_str.replace(',', ''))
        except ValueError:
            return num_str

        if num == 0:
            return "शून्य"
        
        words = []
        if num >= 10000000:
            crores = num // 10000000
            num %= 10000000
            words.append(f"{self._num_to_bhojpuri(str(crores))} करोड़")
        
        if num >= 100000:
            lakhs = num // 100000
            num %= 100000
            words.append(f"{self._num_to_bhojpuri(str(lakhs))} लाख")

        if num >= 1000:
            thousands = num // 1000
            num %= 1000
            words.append(f"{self._num_to_bhojpuri(str(thousands))} हजार")

        if num >= 100:
            hundreds = num // 100
            num %= 100
            words.append(f"{self._num_to_bhojpuri(str(hundreds))} सौ")

        if num > 0:
            s_num = str(num)
            if s_num in self.BHOJPURI_DIGITS:
                words.append(self.BHOJPURI_DIGITS[s_num])
            else:
                words.append(str(num))

        return " ".join(words)

    def normalize_currency(self, text: str) -> str:
        """Convert currency symbols like ₹25,000 -> पच्चीस हजार रुपइया"""
        def replace_rupee(match):
            val = match.group(1).replace(',', '')
            bhojpuri_words = self._num_to_bhojpuri(val)
            return f"{bhojpuri_words} रुपइया"

        t = re.sub(r'₹\s*(\d+(?:,\d+)*)', replace_rupee, text)
        t = re.sub(r'(\d+(?:,\d+)*)\s*(?:रु|रू|rs|rupees)', replace_rupee, t, flags=re.IGNORECASE)
        return t

    def normalize_time(self, text: str) -> str:
        """Convert time like 10:30 AM -> साढ़े दस बजे सवेरे, 4:15 PM -> सवा चार बजे संझा"""
        def replace_time(match):
            hrs = int(match.group(1))
            mins = int(match.group(2))
            period = (match.group(3) or '').upper()

            time_period = "सवेरे"
            if period == 'PM' or hrs >= 12:
                time_period = "संझा"
            
            hrs_word = self.BHOJPURI_DIGITS.get(str(hrs % 12 or 12), str(hrs))
            
            if mins == 0:
                return f"{hrs_word} बजे {time_period}"
            elif mins == 15:
                return f"सवा {hrs_word} बजे {time_period}"
            elif mins == 30:
                return f"साढ़े {hrs_word} बजे {time_period}"
            elif mins == 45:
                next_hr = self.BHOJPURI_DIGITS.get(str((hrs % 12 or 12) + 1), str(hrs + 1))
                return f"पौने {next_hr} बजे {time_period}"
            else:
                mins_word = self._num_to_bhojpuri(str(mins))
                return f"{hrs_word} बजके {mins_word} मिनट {time_period}"

        return re.sub(r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)?', replace_time, text)

    def normalize_percentage(self, text: str) -> str:
        """Convert 50% -> पचास प्रतिशत"""
        def replace_pct(match):
            val = match.group(1)
            bhojpuri_val = self._num_to_bhojpuri(val)
            return f"{bhojpuri_val} प्रतिशत"

        return re.sub(r'(\d+)%', replace_pct, text)

    def normalize_numbers(self, text: str) -> str:
        """Convert raw digits into spoken Bhojpuri numbers."""
        def replace_num(match):
            val = match.group(0)
            return self._num_to_bhojpuri(val)

        return re.sub(r'\b\d+\b', replace_num, text)

    def normalize(self, text: str) -> str:
        """Full normalization pipeline for Bhojpuri speech synthesis."""
        if not text:
            return ""

        t = self.normalize_currency(text)
        t = self.normalize_time(t)
        t = self.normalize_percentage(t)
        t = self.normalize_numbers(t)

        # Standard Bhojpuri punctuation pauses
        t = t.replace('&', ' अउर ')
        t = t.replace('+', ' प्लस ')
        t = re.sub(r'\s+', ' ', t).strip()
        return t

bhojpuri_normalizer = BhojpuriNormalizer()
