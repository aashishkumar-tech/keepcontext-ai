/**
 * Unit tests for the API client.
 */

import * as assert from 'assert';
import { ApiClient, ApiClientError } from '../apiClient';

suite('ApiClient', () => {
    test('ApiClientError has correct properties', () => {
        const err = new ApiClientError('test error', 503, 'agent_error');
        assert.strictEqual(err.message, 'test error');
        assert.strictEqual(err.statusCode, 503);
        assert.strictEqual(err.code, 'agent_error');
        assert.strictEqual(err.name, 'ApiClientError');
    });

    test('ApiClientError defaults', () => {
        const err = new ApiClientError('fail');
        assert.strictEqual(err.statusCode, 0);
        assert.strictEqual(err.code, 'client_error');
    });

    test('ApiClient can be instantiated', () => {
        const client = new ApiClient();
        assert.ok(client);
    });
});
