R_MED = 40
R_HIGH = 70
K_MAX = 3

ESC = "ескалувати"
CLOSE = "закрити як штатну"
ABSENT = "підстави відсутні"
PRESENT = "підстави наявні"
CLARIFY = "потрібне уточнення"
OK = "відповідає"
RETRY = "повторити передачу"
HUMAN = "ескалувати фахівцю"


def risk_level(r, r_med=R_MED, r_high=R_HIGH):
    if r >= r_high:
        return "високий"
    if r >= r_med:
        return "середній"
    return "низький"


def d1(level, over_profile, no_grant, dlp):
    if level == "високий":
        return "R1.1", ESC, "високий", False
    if level == "середній":
        if dlp:
            return "R1.2", ESC, "високий", False
        if over_profile and no_grant:
            return "R1.3", ESC, "середній", False
        return "R1.4", ESC, "середній", True
    if dlp:
        return "R1.5", ESC, "середній", False
    if over_profile and no_grant:
        return "R1.6", ESC, "середній", False
    if over_profile:
        return "R1.7", CLOSE, "низький", True
    return "R1.8", CLOSE, "низький", True


def d1_final(recommendation, override_allowed, soc_override):
    if override_allowed and soc_override:
        return CLOSE if recommendation == ESC else ESC
    return recommendation


def d2(outside, hr_order, prior, dlp):
    aggravating = prior > 0 or dlp
    if outside == 0:
        if aggravating:
            return "R2.2", CLARIFY, True
        return "R2.1", PRESENT, False
    if hr_order:
        if aggravating:
            return "R2.3", CLARIFY, True
        return "R2.4", CLARIFY, False
    if aggravating:
        return "R2.5", ABSENT, True
    return "R2.6", ABSENT, False


def d3(mismatch, attempt, k_max=K_MAX):
    if mismatch == "немає":
        return "R3.1", OK
    if mismatch == "надмірне обмеження":
        return "R3.4", HUMAN
    if attempt < k_max:
        return "R3.2", RETRY
    return "R3.3", HUMAN
