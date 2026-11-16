import random
import re
import time
import unicodedata


def naive_search(text, pattern):
    positions, comparisons = [], 0
    n, m = len(text), len(pattern)
    for i in range(n - m + 1):
        j = 0
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]:
                break
            j += 1
        if j == m:
            positions.append(i)
    return positions, comparisons


def prefix_function(pattern):
    pi = [0] * len(pattern)
    k = 0
    for i in range(1, len(pattern)):
        while k > 0 and pattern[i] != pattern[k]:
            k = pi[k - 1]
        if pattern[i] == pattern[k]:
            k += 1
        pi[i] = k
    return pi


def kmp_search(text, pattern):
    if not pattern:
        return list(range(len(text) + 1)), 0
    pi = prefix_function(pattern)
    positions, comparisons = [], 0
    k = 0
    for i, char in enumerate(text):
        while k > 0 and char != pattern[k]:
            comparisons += 1
            k = pi[k - 1]
        comparisons += 1
        if char == pattern[k]:
            k += 1
        if k == len(pattern):
            positions.append(i - len(pattern) + 1)
            k = pi[k - 1]
    return positions, comparisons


def levenshtein(a, b):
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + (ca != cb)
            ))
        previous = current
    return previous[-1]


def similarity(a, b):
    if not a and not b:
        return 1.0
    return 1 - levenshtein(a, b) / max(len(a), len(b))


TRANSLIT = {
    "а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e",
    "ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m",
    "н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u",
    "ф":"f","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch",
    "ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"
}
LEGAL_FORMS = {"ооо", "оао", "зао", "пао", "ао", "ип"}
ABBREVIATIONS = {
    "ул": "улица",
    "пр": "проспект",
    "пр-т": "проспект",
    "пер": "переулок",
    "д": "дом"
}


def transliterate(text):
    return "".join(TRANSLIT.get(ch, ch) for ch in text)


def normalize_basic(name):
    s = name.lower().replace("ё", "е")
    s = re.sub(r"[\"'«»„“”‘’.,()]", " ", s)
    words = [w for w in s.split() if w not in LEGAL_FORMS]
    return " ".join(words)


def normalize_extended(name):
    s = name.lower().replace("ё", "е")
    s = re.sub(r"[\"'«»„“”‘’.,()]", " ", s)
    words = [ABBREVIATIONS.get(w, w) for w in s.split()]
    words = [w for w in words if w not in LEGAL_FORMS]
    result = transliterate(" ".join(words))
    transliterated_legal_forms = {"ooo", "oao", "zao", "pao", "ao", "ip"}
    return " ".join(w for w in result.split() if w not in transliterated_legal_forms)


def match_records(list_a, list_b, threshold=0.75, normalizer=normalize_extended):
    normalized_b = [(name, normalizer(name)) for name in list_b]
    result = []
    for a in list_a:
        na = normalizer(a)
        best_name, best_score = None, 0.0
        best_kind = "не найдено"
        for b, nb in normalized_b:
            if na == nb:
                best_name, best_score, best_kind = b, 1.0, "точное"
                break
            score = similarity(na, nb)
            if score > best_score:
                best_name, best_score, best_kind = b, score, "нечёткое"
        if best_score >= threshold:
            result.append((a, best_name, best_score, best_kind))
        else:
            result.append((a, None, best_score, "не найдено"))
    return result


if __name__ == "__main__":
    pattern = "aabbaab"
    print("Префикс-функция:", prefix_function(pattern))

    print("\\nСравнение поиска на тексте с повторами")
    print(f"{'n':>10} {'Наивный, с':>14} {'КМП, с':>12} {'Сравн. наив.':>16} {'Сравн. КМП':>14}")
    for n in (10**4, 10**5, 10**6):
        text = ("aabbaac" * ((n + 6) // 7))[:n]
        t0 = time.perf_counter()
        p1, c1 = naive_search(text, pattern)
        naive_time = time.perf_counter() - t0
        t0 = time.perf_counter()
        p2, c2 = kmp_search(text, pattern)
        kmp_time = time.perf_counter() - t0
        assert p1 == p2
        print(f"{n:10d} {naive_time:14.5f} {kmp_time:12.5f} {c1:16d} {c2:14d}")

    print("\\nПроверка Левенштейна")
    for a, b in [("кот", "скот"), ("Ромашка", "Ромашки")]:
        print(a, b, levenshtein(a, b), f"{similarity(a, b):.3f}")

    system_a = [
        'ООО "Ромашка"',
        "АО Василёк",
        "ИП Иванов И.И.",
        "ул. Ленина, 10",
        "ООО «Северный ветер»",
        "пр-т Мира, 5",
        "ООО «Вектор»"
    ]
    system_b = [
        "Ромашка, ООО",
        "ВАСИЛЕК АО",
        "ИП Иванов И.И.",
        "улица Ленина 10",
        "Северный Ветер ООО",
        "проспект Мира, 5",
        "Vektor OOO"
    ]

    basic = match_records(system_a, system_b, 0.75, normalize_basic)
    extended = match_records(system_a, system_b, 0.75, normalize_extended)

    print("\\nСопоставление: базовая нормализация")
    for row in basic:
        print(row)
    print("\\nСопоставление: расширенная нормализация Л7")
    for row in extended:
        print(row)
    print("\\nТочных совпадений: базовая =", sum(x[3] == "точное" for x in basic),
          "; расширенная =", sum(x[3] == "точное" for x in extended))
