from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robot.api import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .smart_element_resolver import SmartElementResolver
import xml.etree.ElementTree as ET
import unicodedata
import re

class AppiumSmartLocator:
    """
    Library Robot Framework para interação inteligente com elementos mobile via Appium.
    """

    def __init__(self):
        self.resolver = SmartElementResolver()

    def _get_driver(self):
        try:
            appium_lib = BuiltIn().get_library_instance("AppiumLibrary")
            return appium_lib._current_application()
        except Exception as e:
            raise RuntimeError(
                "AppiumLibrary não encontrada ou aplicação não aberta. "
                "Você chamou Open Application?"
            ) from e

    @keyword("Resolve Smart Locator")
    def resolver_locator_inteligente(self, descricao_humana, xml_source):
        """
        Retorna o melhor locator possível a partir de uma descrição humana.
        """
        return self.resolver.resolve_locator(descricao_humana, xml_source)

    @keyword("Click Smart Element")
    def clicar_no_elemento(self, descricao_humana):
        """
        Clica em um elemento a partir de uma descrição humana.
        """
        driver = self._get_driver()
        if driver is None:
            raise ValueError("Driver Appium não informado.")

        xml = driver.page_source
        locator = self.resolver.resolve_locator(descricao_humana, xml)
        by, value = self._split_locator(locator)
        driver.find_element(by, value).click()

    @keyword("Type Into Smart Element")
    def preencher_elemento(self, descricao_humana, texto):
        """
        Preenche um campo a partir de uma descrição humana.
        """
        driver = self._get_driver()
        if driver is None:
            raise ValueError("Driver Appium não informado.")

        xml = driver.page_source
        locator = self.resolver.resolve_locator(descricao_humana, xml)
        by, value = self._split_locator(locator)

        el = driver.find_element(by, value)
        el.clear()
        el.send_keys(texto)

    @keyword("Validate Smart Element")
    def validar_elemento(self, descricao_humana, timeout=5):
        """
        Valida se um elemento está presente na tela dentro de um timeout.
        """
        driver = self._get_driver()
        if driver is None:
            raise ValueError("Driver Appium não informado.")

        xml = driver.page_source
        locator = self.resolver.resolve_locator(descricao_humana, xml)
        by, value = self._split_locator(locator)

        logger.info(
            f"Validando elemento '{descricao_humana}' usando locator: "
            f"{locator} (timeout={timeout}s)"
        )

        try:
            WebDriverWait(driver, int(timeout)).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException as e:
            raise AssertionError(
                f"Elemento '{descricao_humana}' não encontrado após {timeout}s. "
                f"Locator usado: {locator}"
            ) from e

    def _split_locator(self, locator: str):
        """
        Converte locator no formato interno para formato aceito pelo Appium.
        """
        if locator.startswith("id="):
            return "id", locator.replace("id=", "", 1)

        if locator.startswith("accessibility_id="):
            return "accessibility id", locator.replace("accessibility_id=", "", 1)

        if locator.startswith("android="):
            return "-android uiautomator", locator.replace("android=", "", 1)

        if locator.startswith("xpath="):
            return "xpath", locator.replace("xpath=", "", 1)

        raise ValueError(f"Locator não suportado: {locator}")
    
    @keyword("Click First Smart Element By Context")

    def click_first_smart_element_by_context(self, context_text):
        """
        Clicks the first actionable element related to a visible text/context.
        Useful for lists/cards where the visible text is not clickable,
        but an icon/button inside the same container is.
        """
        driver = self._get_driver()
        xml = driver.page_source

        root = ET.fromstring(xml)
        parent_map = {child: parent for parent in root.iter() for child in parent}

        anchors = self._find_context_elements(root, context_text)

        if not anchors:
            raise AssertionError(
                f"No element found containing context: '{context_text}'"
            )

        anchors.sort(key=self._element_position)

        anchor = anchors[0]

        logger.info(
            f"[SmartLocator] Context found: '{context_text}' | "
            f"attributes={anchor.attrib}"
        )

        if self._is_clickable(anchor):
            locator = self._build_uiselector_for_element(root, anchor)
            logger.info(
                f"[SmartLocator] Context element is clickable. Using locator: {locator}"
            )
            by, value = self._split_locator(locator)
            driver.find_element(by, value).click()
            return

        container = self._find_clickable_context_container(anchor, parent_map)

        if container is None:
            raise AssertionError(
                f"Context '{context_text}' was found, but no related container was found."
            )

        candidates = self._find_clickable_children(container)

        if not candidates:
            raise AssertionError(
                f"Context '{context_text}' was found, but no clickable child was found."
            )

        ranked = self._rank_clickable_candidates(candidates)
        best_priority = ranked[0][0]
        best_candidates = [element for priority, element in ranked if priority == best_priority]

        if len(best_candidates) == 1:
            candidate = best_candidates[0]
            locator = self._build_uiselector_for_element(root, candidate)

            logger.info(
                f"[SmartLocator] Single clickable candidate found. Using locator: {locator}"
            )

            by, value = self._split_locator(locator)
            driver.find_element(by, value).click()
            return

        self._log_ambiguous_clickable_candidates(root, context_text, best_candidates)

        raise AssertionError(
            f"Multiple clickable candidates found for context '{context_text}'. "
            f"Check the Robot log for suggested locators."
        )
    
    def _find_context_elements(self, root, context_text):
        target = self._normalize(context_text)
        elements = []
    
        for el in root.iter():
            text = self._normalize(el.attrib.get("text", ""))
            content_desc = self._normalize(el.attrib.get("content-desc", ""))
    
            if target in text or target in content_desc:
                if self._is_displayed(el):
                    elements.append(el)
    
        return elements
    
    
    def _find_clickable_context_container(self, anchor, parent_map, max_levels=4):
        current = anchor
    
        for _ in range(max_levels):
            parent = parent_map.get(current)
            if parent is None:
                return current
    
            clickable_children = self._find_clickable_children(parent)
    
            if clickable_children:
                return parent
    
            current = parent
    
        return current
    
    
    def _find_clickable_children(self, container):
        candidates = []
    
        for el in container.iter():
            if self._is_clickable(el) and self._is_displayed(el):
                candidates.append(el)
    
        return candidates
    
    
    def _rank_clickable_candidates(self, candidates):
        ranked = []
    
        for el in candidates:
            text = el.attrib.get("text", "").strip()
            content_desc = el.attrib.get("content-desc", "").strip()
    
            if not text and not content_desc:
                priority = 1
            elif not text and content_desc:
                priority = 2
            elif text:
                priority = 3
            else:
                priority = 4
    
            ranked.append((priority, el))
    
        ranked.sort(key=lambda item: (item[0], self._element_position(item[1])))
        return ranked
    
    
    def _log_ambiguous_clickable_candidates(self, root, context_text, candidates):
        logger.warn(
            f"[SmartLocator] Multiple clickable candidates found for context: '{context_text}'"
        )
    
        for index, candidate in enumerate(candidates, start=1):
            locator = self._build_uiselector_for_element(root, candidate)
    
            logger.warn(
                "\n"
                f"[SmartLocator] Candidate {index}\n"
                f"  text: {candidate.attrib.get('text', '')}\n"
                f"  content-desc: {candidate.attrib.get('content-desc', '')}\n"
                f"  resource-id: {candidate.attrib.get('resource-id', '')}\n"
                f"  class: {candidate.attrib.get('class', '')}\n"
                f"  bounds: {candidate.attrib.get('bounds', '')}\n"
                f"  Suggested Robot keyword:\n"
                f"  Click Element    {locator}"
            )
    
    
    def _build_uiselector_for_element(self, root, element):
        attrib = element.attrib
    
        resource_id = attrib.get("resource-id")
        if resource_id:
            instance = self._calculate_instance(
                root,
                lambda el: el.attrib.get("resource-id") == resource_id,
                element,
            )
            return (
                f'android=new UiSelector()'
                f'.resourceId("{resource_id}")'
                f'.instance({instance})'
            )
    
        content_desc = attrib.get("content-desc")
        if content_desc:
            instance = self._calculate_instance(
                root,
                lambda el: el.attrib.get("content-desc") == content_desc,
                element,
            )
            return (
                f'android=new UiSelector()'
                f'.description("{content_desc}")'
                f'.instance({instance})'
            )
    
        text = attrib.get("text")
        if text:
            instance = self._calculate_instance(
                root,
                lambda el: el.attrib.get("text") == text,
                element,
            )
            return (
                f'android=new UiSelector()'
                f'.text("{text}")'
                f'.instance({instance})'
            )
    
        class_name = attrib.get("class")
        if class_name:
            instance = self._calculate_instance(
                root,
                lambda el: el.attrib.get("class") == class_name,
                element,
            )
            return (
                f'android=new UiSelector()'
                f'.className("{class_name}")'
                f'.instance({instance})'
            )
    
        raise ValueError(f"Could not build UiSelector for element: {attrib}")
    
    
    def _calculate_instance(self, root, matcher, target_element):
        instance = 0
    
        for el in root.iter():
            if matcher(el):
                if el is target_element:
                    return instance
                instance += 1
    
        return 0
    
    
    def _is_clickable(self, element):
        return element.attrib.get("clickable", "").lower() == "true"
    
    
    def _is_displayed(self, element):
        displayed = element.attrib.get("displayed")
        visible = element.attrib.get("visible")
    
        if displayed is not None:
            return displayed.lower() == "true"
    
        if visible is not None:
            return visible.lower() == "true"
    
        return True
    
    
    def _element_position(self, element):
        bounds = element.attrib.get("bounds", "")
        match = re.search(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
    
        if not match:
            return (999999, 999999)
    
        x1, y1, _, _ = map(int, match.groups())
        return (y1, x1)
    
    
    def _normalize(self, value):
        if not value:
            return ""
    
        value = value.lower().strip()
        value = unicodedata.normalize("NFD", value)
        value = "".join(c for c in value if unicodedata.category(c) != "Mn")
        return " ".join(value.split())