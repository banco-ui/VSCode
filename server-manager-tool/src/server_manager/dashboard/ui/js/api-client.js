/* Server Manager Dashboard — API Client (Phase 23)
 *
 * Thin wrapper around fetch() that calls Phase 22 Management API endpoints.
 *
 * SAFETY:
 *   - Only GET (read-only) and POST /preview endpoints are used.
 *   - No PUT, DELETE, or PATCH calls.
 *   - No credential storage (no localStorage for tokens/passwords).
 *   - No direct provider API calls.
 *   - No shell command invocation.
 *   - All responses are parsed as JSON; errors are surfaced safely.
 */

(function (global) {
  'use strict';

  const BASE = '/api/v1';

  /**
   * Wrapper around fetch that handles errors safely.
   * @param {string} path — API path relative to BASE
   * @param {object} options — fetch options
   * @returns {Promise<object>} parsed JSON response
   * @throws {ApiError} on non-2xx responses
   */
  async function _request(path, options) {
    const url = BASE + path;
    let resp;
    try {
      resp = await fetch(url, options || {});
    } catch (e) {
      throw new ApiError('NETWORK_ERROR', 'Unable to reach the API server.', 0);
    }
    let body = null;
    try { body = await resp.json(); } catch (_) { /* non-JSON response */ }
    if (!resp.ok) {
      const err = (body && body.error) || {};
      throw new ApiError(
        err.code || 'HTTP_ERROR',
        err.message || 'Request failed with status ' + resp.status,
        resp.status
      );
    }
    return body;
  }

  /** Custom error type with code + HTTP status. */
  class ApiError extends Error {
    constructor(code, message, status) {
      super(message);
      this.name = 'ApiError';
      this.code = code;
      this.status = status;
    }
  }

  const ApiClient = {
    ApiError: ApiError,

    // ── System ──────────────────────────────────────────────
    getSystemHealth: () => _request('/system/health'),
    getSystemReadiness: () => _request('/system/readiness'),

    // ── Inventory ────────────────────────────────────────────
    getInventorySummary: () => _request('/inventory'),
    listEntities: (entityType) => {
      const q = entityType ? '?entity_type=' + encodeURIComponent(entityType) : '';
      return _request('/inventory/entities' + q);
    },
    getEntity: (id) => _request('/inventory/entities/' + encodeURIComponent(id)),
    listPlatforms: () => _request('/inventory/platforms'),
    listClusters: () => _request('/inventory/clusters'),
    listNodes: () => _request('/inventory/nodes'),
    listExecutionEnvironments: () => _request('/inventory/execution-environments'),
    listNetworks: () => _request('/inventory/networks'),
    listStorages: () => _request('/inventory/storages'),

    // ── Health ───────────────────────────────────────────────
    getHealthReport: () => _request('/health'),
    getEntityHealth: (id) => _request('/health/entities/' + encodeURIComponent(id)),

    // ── Graph ────────────────────────────────────────────────
    getGraphSummary: () => _request('/graph/summary'),
    getGraphNode: (id) => _request('/graph/nodes/' + encodeURIComponent(id)),
    getNodeRelationships: (id) => _request('/graph/nodes/' + encodeURIComponent(id) + '/relationships'),
    getNodeNeighbors: (id) => _request('/graph/nodes/' + encodeURIComponent(id) + '/neighbors'),

    // ── Monitoring ───────────────────────────────────────────
    listObservations: () => _request('/monitoring/observations'),
    getEntityObservations: (id) => _request('/monitoring/observations/' + encodeURIComponent(id)),

    // ── Faults ───────────────────────────────────────────────
    listFaults: (status) => {
      const q = status ? '?status=' + encodeURIComponent(status) : '';
      return _request('/faults' + q);
    },
    getFault: (id) => _request('/faults/' + encodeURIComponent(id)),
    getEntityFaults: (id) => _request('/faults/entities/' + encodeURIComponent(id)),

    // ── Visibility ───────────────────────────────────────────
    getVisibilitySummary: () => _request('/visibility/summary'),
    listVisibilityAlerts: (status) => {
      const q = status ? '?status=' + encodeURIComponent(status) : '';
      return _request('/visibility/alerts' + q);
    },
    getVisibilityAlert: (id) => _request('/visibility/alerts/' + encodeURIComponent(id)),
    getEntityStatus: (id) => _request('/visibility/entities/' + encodeURIComponent(id)),

    // ── Operations Preview (POST — no auto-repeat) ───────────
    previewOperation: (body) => _request('/operations/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),

    // ── Recovery Preview (POST — no auto-repeat) ─────────────
    previewRecovery: (body) => _request('/recovery/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  };

  global.ApiClient = ApiClient;
})(window);
