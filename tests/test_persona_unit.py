import unittest
from app.concierge.persona import get_persona, KYNIKOS, LEO, MUEVE

class TestPersona(unittest.TestCase):
    def test_get_persona_existing(self):
        self.assertEqual(get_persona("kynikos"), KYNIKOS)
        self.assertEqual(get_persona("leo"), LEO)
        self.assertEqual(get_persona("mueve"), MUEVE)

    def test_get_persona_case_insensitive(self):
        self.assertEqual(get_persona("KYNIKOS"), KYNIKOS)
        self.assertEqual(get_persona("Leo"), LEO)

    def test_get_persona_default(self):
        self.assertEqual(get_persona("nonexistent"), KYNIKOS)

if __name__ == "__main__":
    unittest.main()
