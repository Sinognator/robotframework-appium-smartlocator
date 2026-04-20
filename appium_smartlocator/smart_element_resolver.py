from .semantic_parser import SemanticParser
from .element_resolver import ElementResolver
from .locator_builder import LocatorBuilder


class SmartElementResolver:
    def __init__(self):
        self.parser = SemanticParser()
        self.resolver = ElementResolver()
        self.locator_builder = LocatorBuilder()

    def resolve_locator(self, descricao_humana: str, xml_source: str) -> str:
        if not descricao_humana or not descricao_humana.strip():
            raise ValueError("A descrição humana não pode ser vazia.")

        if not xml_source or not xml_source.strip():
            raise ValueError("O XML da página não pode ser vazio.")

        parsed = self.parser.parse(descricao_humana)
        candidates = self.resolver.resolve(parsed, xml_source)

        if not candidates:
            raise LookupError(
                f"Nenhum elemento encontrado para '{descricao_humana}'. "
                f"Tipo interpretado='{parsed.tipo}', "
                f"identificador='{parsed.identificador}'."
            )

        best_candidate = candidates[0]
        return self.locator_builder.build(best_candidate.element)

    def resolve_candidates(self, descricao_humana: str, xml_source: str):
        """
        Retorna os candidatos encontrados para debug.
        """
        if not descricao_humana or not descricao_humana.strip():
            raise ValueError("A descrição humana não pode ser vazia.")

        if not xml_source or not xml_source.strip():
            raise ValueError("O XML da página não pode ser vazio.")

        parsed = self.parser.parse(descricao_humana)
        return self.resolver.resolve(parsed, xml_source)