import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app


class ChatTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_context_is_delegated_without_current_message_duplication(self):
        history = [{'role': 'user', 'content': 'I am Sam'}, {'role': 'assistant', 'content': 'Hello Sam'}]
        with patch('main.generate_response', return_value='Sam.') as generate:
            response = self.client.post('/chat', json={'message': 'My name?', 'history': history})
        generate.assert_called_once_with('My name?', history)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'response': 'Sam.'})

    def test_first_turn(self):
        with patch('main.generate_response', return_value='Hello!') as generate:
            response = self.client.post('/chat', json={'message': 'Hello'})
        generate.assert_called_once_with('Hello', [])
        self.assertEqual(response.status_code, 200)

    def test_provider_errors_are_clean(self):
        for error, expected in [(RuntimeError('secret'), 502), (TimeoutError('secret'), 504), (NotImplementedError('secret'), 503)]:
            with self.subTest(error=error), patch('main.generate_response', side_effect=error):
                response = self.client.post('/chat', json={'message': 'Hello'})
                self.assertEqual(response.status_code, expected)
                self.assertIsInstance(response.json()['detail'], str)
                self.assertNotIn('secret', response.text)

    def test_invalid_provider_output(self):
        for value in ['', '   ', None, {'response': 'wrong type'}]:
            with self.subTest(value=value), patch('main.generate_response', return_value=value):
                self.assertEqual(self.client.post('/chat', json={'message': 'Hi'}).status_code, 502)

    def test_validation_prevents_generation(self):
        with patch('main.generate_response') as generate:
            for payload in [{'message': ' '}, {'message': 'Hi', 'history': [{'role': 'system', 'content': 'x'}]}]:
                self.assertEqual(self.client.post('/chat', json=payload).status_code, 422)
        generate.assert_not_called()

    def test_cors_preflight(self):
        response = self.client.options('/chat', headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST', 'Access-Control-Request-Headers': 'content-type'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['access-control-allow-origin'], 'http://localhost:5173')


if __name__ == '__main__':
    unittest.main()
