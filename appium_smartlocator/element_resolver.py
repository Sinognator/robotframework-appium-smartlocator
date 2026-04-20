import xml.etree.ElementTree as ET
import unicodedata
from dataclasses import dataclass
from .semantic_parser import ParsedElement


ANDROID_CLASS_BY_TYPE = {
    "botao": ["android.widget.Button", "android.view.View"],
    "link": ["android.widget.TextView", "android.view.View"],
    "campo": ["android.widget.EditText"],
    "texto": ["android.widget.TextView", "android.view.View"],
    "dropdown": ["android.widget.Spinner"],
    "checkbox": ["android.widget.CheckBox"],
    "radio": ["android.widget.RadioButton"],
    "icone": ["android.widget.ImageView", "android.view.View"],
    "switch": ["android.widget.Switch"],
    # "url" propositalmente sem filtro rígido de class
}


@dataclass
class ElementCandidate:
    element: ET.Element
    score: int
    reasons: list[str]


class ElementResolver:
    def resolve(self, parsed: ParsedElement, xml_source: str) -> list[ElementCandidate]:
        root = ET.fromstring(xml_source)
        candidates = []

        allowed_classes = ANDROID_CLASS_BY_TYPE.get(parsed.tipo, [])

        for el in root.iter():
            if not self._matches_type(el, parsed.tipo, allowed_classes):
                continue

            score, reasons = self._score_element(el, parsed)

            if score > 0:
                candidates.append(ElementCandidate(el, score, reasons))

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates

    def _matches_type(self, el: ET.Element, tipo: str, allowed_classes: list[str]) -> bool:
        el_class = el.attrib.get("class", "")

        # Se não houver regra para o tipo, não filtra por classe
        if not allowed_classes:
            return True

        # Match exato
        if el_class in allowed_classes:
            return True

        # Flexibilização controlada para alguns tipos
        if tipo in {"botao", "link", "texto", "icone"} and el_class == "android.view.View":
            return True

        return False

    def _normalize_text(self, value: str) -> str:
        if not value:
            return ""

        value = value.lower().strip()
        value = unicodedata.normalize("NFD", value)
        value = "".join(c for c in value if unicodedata.category(c) != "Mn")
        value = value.replace("-", " ")
        value = value.replace("_", " ")
        value = value.replace(":", " ")
        return " ".join(value.split())

    def _score_element(self, el: ET.Element, parsed: ParsedElement) -> tuple[int, list[str]]:
        score = 0
        reasons = []

        target = self._normalize_text(parsed.identificador)

        # Atributos principais
        for attr, weight_equal, weight_contains in [
            ("text", 60, 35),
            ("content-desc", 55, 30),
            ("resource-id", 45, 25),
            ("hint", 35, 20),
        ]:
            value = el.attrib.get(attr)
            if not value:
                continue

            value_norm = self._normalize_text(value)

            if target == value_norm:
                score += weight_equal
                reasons.append(f"{attr} == '{target}'")
            elif len(target) >= 3 and target in value_norm:
                score += weight_contains
                reasons.append(f"{attr} contains '{target}'")

        # Bônus por estado útil
        if el.attrib.get("displayed", "").lower() == "true":
            score += 10
            reasons.append("displayed=true")

        if el.attrib.get("enabled", "").lower() == "true":
            score += 5
            reasons.append("enabled=true")

        if parsed.tipo in {"botao", "link", "icone"} and el.attrib.get("clickable", "").lower() == "true":
            score += 10
            reasons.append("clickable=true")

        if parsed.tipo == "campo" and el.attrib.get("focusable", "").lower() == "true":
            score += 10
            reasons.append("focusable=true")

        return score, reasons