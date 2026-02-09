import unittest
from unittest.mock import MagicMock, patch
from app.crud.utils import get_currency_exchange_rates

class TestCurrencyFunctions(unittest.TestCase):
    def setUp(self):
        self.db = MagicMock()  # Mocking the database session
        self.db.execute.side_effect = [
            [{'name': 'USD', 'conversion_rate': 1.0}, {'name': 'EUR', 'conversion_rate': 0.9}],
            [{'name': 'USD', 'conversion_rate': 1.0}, {'name': 'EUR', 'conversion_rate': 0.85}]  # Different rate for different call
        ]

    @patch('app.crud.utils.TTLCache')
    def test_cache_hit(self, MockTTLCache):
        # Mock the TTLCache instance
        mock_cache = MockTTLCache.return_value
        mock_cache.get = MagicMock(side_effect=lambda key: None)  # Simulate cache miss initially
        mock_cache.__setitem__ = MagicMock()  # Simulate setting cache
        
        # Call the function once (cache miss)
        result1 = get_currency_exchange_rates(self.db, 'USD')
        
        # Call the function again (cache hit)
        result2 = get_currency_exchange_rates(self.db, 'USD')
        
        # Check that db.execute was called only once (cache hit on second call)
        self.db.execute.assert_called_once()
        # Check that results are the same
        self.assertEqual(result1, result2)

    @patch('app.crud.utils.TTLCache')
    def test_cache_miss(self, MockTTLCache):
        # Mock the TTLCache instance
        mock_cache = MockTTLCache.return_value
        mock_cache.get = MagicMock(side_effect=lambda key: None)  # Simulate cache miss
        mock_cache.__setitem__ = MagicMock()  # Simulate setting cache

        # Call the function with different parameters
        result1 = get_currency_exchange_rates(self.db, 'USD')
        result2 = get_currency_exchange_rates(self.db, 'EUR')

        # Ensure db.execute is called twice with different parameters
        self.assertEqual(self.db.execute.call_count, 2)

        # Check if the results are different for different queries
        self.assertNotEqual(result1, result2)

if __name__ == '__main__':
    unittest.main()
