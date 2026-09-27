import copy
import json
import unittest
from unittest.mock import patch

import anthropic
import httpx
from fastapi.testclient import TestClient

from llm_provider import generate_response
from main import app


class ProviderTests(unittest.TestCase):
    def setUp(self):
        key = patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'})
        key.start()
        self.addCleanup(key.stop)

    def mock_api(self, handler):
        client = anthropic.Anthropic(
            api_key='test-key', max_retries=0,
            http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        return patch('llm_provider.anthropic.Anthropic', return_value=client)

    def test_sdk_request_and_route_response(self):
        history = [{'role': 'user', 'content': 'I am Sam'}, {'role': 'assistant', 'content': 'Hello Sam'}]
        original = copy.deepcopy(history)

        def handler(request):
            self.assertEqual(request.url.path, '/v1/messages')
            self.assertEqual(request.headers['x-api-key'], 'test-key')
            body = json.loads(request.content)
            self.assertEqual(body['model'], 'claude-sonnet-4-5')
            self.assertEqual(body['max_tokens'], 1024)
            self.assertEqual(body['messages'], original + [{'role': 'user', 'content': 'My name?'}])
            return httpx.Response(200, json={
                'id': 'msg_test', 'type': 'message', 'role': 'assistant',
                'model': 'claude-sonnet-4-5', 'stop_reason': 'end_turn',
                'content': [{'type': 'text', 'text': 'Sam.'}, {'type': 'text', 'text': 'Hello!'}],
                'usage': {'input_tokens': 10, 'output_tokens': 5},
            })

        with self.mock_api(handler) as factory:
            self.assertEqual(generate_response('My name?', history), 'Sam.\nHello!')
            factory.assert_called_once_with(api_key='test-key', timeout=60.0, max_retries=0)
        self.assertEqual(history, original)
        with self.mock_api(handler):
            response = TestClient(app).post('/chat', json={'message': 'My name?', 'history': history})
        self.assertEqual(response.json(), {'response': 'Sam.\nHello!'})

    def test_sdk_failures_are_sanitized(self):
        for status in [401, 429, 500]:
            with self.subTest(status=status):
                with self.mock_api(lambda request: httpx.Response(status, json={'error': {'message': 'sensitive details'}})):
                    with self.assertRaisesRegex(RuntimeError, '^The AI service could not complete the request'):
                        generate_response('Hello', [])

    def test_timeout_maps_to_builtin_timeout(self):
        def handler(request):
            raise httpx.ReadTimeout('private details', request=request)
        with self.mock_api(handler):
            with self.assertRaisesRegex(TimeoutError, '^The AI service took too long'):
                generate_response('Hello', [])

    def test_missing_key_does_not_create_client(self):
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}), patch('llm_provider.anthropic.Anthropic') as factory:
            with self.assertRaisesRegex(RuntimeError, 'Set ANTHROPIC_API_KEY'):
                generate_response('Hello', [])
        factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
