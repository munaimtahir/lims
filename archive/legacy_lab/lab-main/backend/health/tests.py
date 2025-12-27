from unittest.mock import patch

from django.test import Client, TestCase


class HealthCheckTestCase(TestCase):
    """Test cases for health check endpoint."""

    def setUp(self):
        """Set up test client."""
        self.client = Client()

    def test_health_check(self):
        """Test health check endpoint returns healthy status."""
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertIn("cache", data)
        # Status should be healthy or degraded
        self.assertIn(data["status"], ["healthy", "degraded"])

    def test_health_check_database_probe(self):
        """Test database connectivity in health check."""
        response = self.client.get("/api/health/")
        data = response.json()
        # Database should be healthy in tests
        self.assertEqual(data["database"], "healthy")

    def test_health_check_cache_probe(self):
        """Test cache connectivity in health check."""
        response = self.client.get("/api/health/")
        data = response.json()
        # Cache status should be present
        self.assertIn("cache", data)

    @patch("django.db.connection.ensure_connection")
    def test_health_check_database_failure(self, mock_ensure_connection):
        """Test health check when database is down."""
        mock_ensure_connection.side_effect = Exception("Database connection failed")
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("unhealthy", data["database"])

    @patch("django.core.cache.cache.set")
    def test_health_check_cache_set_failure(self, mock_cache_set):
        """Test health check when cache set fails."""
        mock_cache_set.side_effect = Exception("Cache connection failed")
        response = self.client.get("/api/health/")
        # Cache failure is not critical if DB is healthy
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "degraded")
        self.assertIn("unhealthy", data["cache"])

    @patch("django.core.cache.cache.get")
    @patch("django.core.cache.cache.set")
    def test_health_check_cache_get_failure(self, mock_cache_set, mock_cache_get):
        """Test health check when cache get returns wrong value."""
        mock_cache_set.return_value = None
        mock_cache_get.return_value = None  # Not 'ok'
        response = self.client.get("/api/health/")
        self.assertEqual(response.status_code, 503)
        data = response.json()
        self.assertEqual(data["status"], "degraded")
        self.assertIn("unhealthy", data["cache"])
