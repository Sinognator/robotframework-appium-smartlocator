import xml.etree.ElementTree as ET

class LocatorBuilder:

    def build(self, candidate: ET.Element) -> str:
        attrib = candidate.attrib

        # 1. resource-id (melhor opção)
        resource_id = attrib.get("resource-id")
        if resource_id:
            clean_id = self._extract_id(resource_id)
            return f"id={clean_id}"

        # 2. accessibility id
        content_desc = attrib.get("content-desc")
        if content_desc:
            return f"accessibility_id={content_desc.strip()}"

        # 3. UiSelector (mais robusto)
        ui_selector = self._build_ui_selector(attrib)
        if ui_selector:
            return ui_selector

        # 4. XPath melhorado
        xpath = self._build_short_xpath(attrib)
        if xpath:
            return xpath

        # 5. fallback mais controlado
        return self._fallback_xpath(attrib)

    # --------------------------------------------------

    def _extract_id(self, resource_id: str) -> str:
        """
        Remove package do resource-id
        Ex: com.app:id/btn_login -> btn_login
        """
        if "/" in resource_id:
            return resource_id.split("/")[-1]
        return resource_id

    # --------------------------------------------------

    def _build_ui_selector(self, attrib: dict) -> str:
        parts = []

        class_name = attrib.get("class")
        if class_name:
            parts.append(f'.className("{class_name}")')

        text = attrib.get("text")
        if text:
            parts.append(f'.textContains("{text}")')

        content_desc = attrib.get("content-desc")
        if content_desc:
            parts.append(f'.descriptionContains("{content_desc}")')

        resource_id = attrib.get("resource-id")
        if resource_id:
            parts.append(f'.resourceId("{resource_id}")')

        if not parts:
            return None

        return "android=new UiSelector()" + "".join(parts)

    # --------------------------------------------------

    def _build_short_xpath(self, attrib: dict) -> str:
        class_name = attrib.get("class")
        text = attrib.get("text")

        if class_name and text:
            text = self._escape_xpath(text)
            return f'xpath=//{class_name}[@text="{text}"]'

        if class_name:
            return f"xpath=//{class_name}"

        return None

    # --------------------------------------------------

    def _fallback_xpath(self, attrib: dict) -> str:
        """
        fallback mais inteligente que //*.
        """
        class_name = attrib.get("class")
        if class_name:
            return f"xpath=//{class_name}[1]"

        return "xpath=//*"

    # --------------------------------------------------

    def _escape_xpath(self, text: str) -> str:
        """
        Evita quebrar XPath com aspas
        """
        return text.replace('"', '\\"')