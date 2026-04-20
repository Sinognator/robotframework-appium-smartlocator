import unicodedata
from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class ParsedElement:
    tipo: str
    identificador: str
    acao: str
    raw_text: str


class SemanticParser:
    TYPE_SYNONYMS = {
        "botao": ["botao", "botão", "btn", "action"],
        "link": ["link", "saiba", "ancora", "âncora"],
        "campo": ["campo", "input", "edit", "campo de texto"],
        "texto": ["texto", "label", "mensagem", "titulo", "título"],
        "dropdown": ["dropdown", "combo", "lista suspensa", "spinner"],
        "checkbox": ["checkbox", "check", "marcar"],
        "radio": ["radio", "opcao", "opção"],
        "icone": ["icone", "ícone", "icon"],
        "url": ["url", "endereco", "endereço"],
        "switch": ["switch", "toggle", "chave"],
    }

    DEFAULT_ACTION_BY_TYPE = {
        "botao": "clicar",
        "icone": "clicar",
        "campo": "preencher",
        "dropdown": "selecionar",
        "checkbox": "marcar",
        "radio": "selecionar",
        "switch": "alternar",
        "texto": "validar",
        "link": "clicar",
        "url": "validar",
    }

    STOPWORDS = {
        "no", "na", "nos", "nas",
        "do", "da", "dos", "das",
        "de", "para", "o", "a", "os", "as"
    }

    def parse(self, text: str) -> ParsedElement:
        normalized = self._normalize(text)

        tipo, termo_encontrado = self._resolve_type(normalized)
        if not tipo:
            raise ValueError(f"Tipo de elemento não reconhecido em: '{text}'")

        identificador = self._extract_identifier(normalized, termo_encontrado)
        if not identificador:
            raise ValueError(f"Identificador não declarado em: '{text}'")

        acao = self.DEFAULT_ACTION_BY_TYPE.get(tipo, "interagir")

        return ParsedElement(
            tipo=tipo,
            identificador=identificador,
            acao=acao,
            raw_text=text,
        )

    def _resolve_type(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        # Prioriza termos compostos maiores primeiro
        candidates = []
        for canonical, synonyms in self.TYPE_SYNONYMS.items():
            for synonym in synonyms:
                synonym_norm = self._normalize(synonym)
                candidates.append((canonical, synonym_norm))

        candidates.sort(key=lambda item: len(item[1]), reverse=True)

        for canonical, synonym in candidates:
            if self._contains_term(text, synonym):
                return canonical, synonym

        return None, None

    def _extract_identifier(self, text: str, termo_encontrado: str) -> str:
        text = self._remove_first_term(text, termo_encontrado)

        tokens = [token for token in text.split() if token not in self.STOPWORDS]
        return " ".join(tokens).strip()

    def _contains_term(self, text: str, term: str) -> bool:
        padded_text = f" {text} "
        padded_term = f" {term} "
        return padded_term in padded_text

    def _remove_first_term(self, text: str, term: str) -> str:
        padded_text = f" {text} "
        padded_term = f" {term} "

        idx = padded_text.find(padded_term)
        if idx == -1:
            return text

        result = (
            padded_text[:idx] +
            " " +
            padded_text[idx + len(padded_term):]
        )
        return " ".join(result.split())

    def _normalize(self, text: str) -> str:
        text = text.lower().strip()
        text = unicodedata.normalize("NFD", text)
        text = "".join(
            c for c in text if unicodedata.category(c) != "Mn"
        )
        return " ".join(text.split())