"""Conservative catalogue prefilter. Ambiguous or inconsistent labels require detail."""
import re

def norm_title(value):
    return ' '.join(str(value or '').lower().replace('ё','е').split())

# Only clear occupational labels, never generic words such as analyst or manager.
_NON_TARGET = re.compile(
    r'^(?:(?:старший|младший|ведущий|senior|junior|middle)\s+)*'
    r'(?:аналитик данных|data analyst|data scientist|data engineer|'
    r'бизнес[- ]аналитик|системный аналитик|'
    r'(?:bi|backend|frontend|fullstack|full-stack|java|python|go|ios|android)[- ]разработчик|'
    r'разработчик|инженер по тестированию|qa engineer|'
    r'дизайнер|product designer|project manager|менеджер проектов|'
    r'рекрутер|бухгалтер)(?=\s|[,.:()—–-]|$)',re.I)
_TARGET_HINT=re.compile(r'продуктов\w*\s+аналитик|аналитик\w*\s+(?:по\s+)?продукт|product analy|product manag|product owner|продакт|менеджер\w*\s+(?:по\s+развитию\s+|по\s+)?продукт|\bapm\b',re.I)

def can_skip_catalog(labels, verified_title, classify):
    # Only reuse a previously verified detail title, when every nonempty
    # catalogue label agrees exactly. New vacancies always get a detail fetch.
    actual=norm_title(verified_title)
    names={norm_title(label) for label in labels if norm_title(label)}
    return bool(actual and names=={actual} and not classify(actual)
                and _NON_TARGET.search(actual) and not _TARGET_HINT.search(actual))
