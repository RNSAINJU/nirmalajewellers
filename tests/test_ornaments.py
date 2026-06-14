from django.test import TestCase

from ornament.models import Kaligar, Ornament


class OrnamentQueryTest(TestCase):
    """Smoke test for ornament model queries used in order assignment."""

    def test_unassigned_ornaments_query(self):
        kaligar = Kaligar.objects.create(name='Test Kaligar', panno='123456789')
        Ornament.objects.create(
            code='TEST-001',
            ornament_name='Test Ring',
            metal_type='Gold',
            weight=10,
            kaligar=kaligar,
        )

        self.assertEqual(Ornament.objects.count(), 1)
        self.assertEqual(Ornament.objects.filter(order__isnull=True).count(), 1)
