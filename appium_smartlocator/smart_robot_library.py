from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
from robot.api import logger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from .smart_element_resolver import SmartElementResolver


class SmartMobileLibrary:
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

    @keyword("Resolver Locator Inteligente")
    def resolver_locator_inteligente(self, descricao_humana, xml_source):
        """
        Retorna o melhor locator possível a partir de uma descrição humana.
        """
        return self.resolver.resolve_locator(descricao_humana, xml_source)

    @keyword("Clicar No Elemento")
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

    @keyword("Preencher Elemento")
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

    @keyword("Validar Elemento")
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