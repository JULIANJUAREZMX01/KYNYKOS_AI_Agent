import unittest
from app.skills.hvac_triage import detect_hvac_issue, generate_hvac_response, get_ticket_priority, HVAC_KB

class TestHVACTriage(unittest.TestCase):
    def test_detect_hvac_issue_known(self):
        # Test "no enfría" -> no_enfria
        key, data = detect_hvac_issue("mi aire no enfría")
        self.assertEqual(key, "no_enfria")
        self.assertEqual(data, HVAC_KB["no_enfria"])

        # Test "ruido" -> ruido_raro
        key, data = detect_hvac_issue("el ac hace ruido")
        self.assertEqual(key, "ruido_raro")
        self.assertEqual(data, HVAC_KB["ruido_raro"])

        # Test "gotea" -> gotea_agua
        key, data = detect_hvac_issue("clima gotea")
        self.assertEqual(key, "gotea_agua")
        self.assertEqual(data, HVAC_KB["gotea_agua"])

        # Test "no enciende" -> no_enciende
        key, data = detect_hvac_issue("no enciende el acondicionador")
        self.assertEqual(key, "no_enciende")
        self.assertEqual(data, HVAC_KB["no_enciende"])

        # Test "aire caliente" -> no_enfria
        key, data = detect_hvac_issue("sale aire caliente del ac")
        self.assertEqual(key, "no_enfria")

    def test_detect_hvac_issue_edge_cases(self):
        # Case insensitivity
        key, _ = detect_hvac_issue("AIRE ACONDICIONADO NO FUNCIONA")
        self.assertEqual(key, "no_enciende")

        # No HVAC keyword
        key, data = detect_hvac_issue("hola, como estas?")
        self.assertIsNone(key)
        self.assertIsNone(data)

        # HVAC keyword but unknown issue
        key, data = detect_hvac_issue("mi aire acondicionado se ve raro")
        self.assertEqual(key, "unknown")
        self.assertEqual(data["descripcion"], "Problema con AC")

    def test_generate_hvac_response(self):
        # Known key
        key = "no_enfria"
        data = HVAC_KB[key]
        response = generate_hvac_response(key, data, "habitación 101")
        self.assertIn("AC no enfría / aire caliente", response)
        self.assertIn("habitación 101", response)
        self.assertIn("Prioridad media", response)

        # Unknown key
        response = generate_hvac_response("unknown", {}, "suite presidential")
        self.assertIn("Reporte de AC en suite presidential recibido", response)
        self.assertIn("¿El AC no enfría, hace ruido, gotea o no enciende?", response)

    def test_get_ticket_priority(self):
        self.assertEqual(get_ticket_priority("no_enfria"), "media")
        self.assertEqual(get_ticket_priority("ruido_raro"), "baja")
        self.assertEqual(get_ticket_priority("gotea_agua"), "alta")
        self.assertEqual(get_ticket_priority("no_enciende"), "alta")
        self.assertEqual(get_ticket_priority("random"), "media")

if __name__ == "__main__":
    unittest.main()
