def render(operation, c, status, result, replayed, original, settings, now, time, wire, started):
    payload = result if status >= 400 else {'data': result, 'meta': {'request_id': c.request_id, 'server_time': wire(now()), 'contract_version': VERSION, 'replayed': replayed, 'original_request_id': original}}
    schema = operation['responses'].get(str(status), {}).get('content', {}).get('application/json', {}).get('schema')
    if schema is None or violations(schema, wire(payload)):
        status = 500
        payload = Rejected('INTERNAL_ERROR').payload(c.request_id)
    headers = {'X-Request-ID': c.request_id, 'Cache-Control': 'no-store', 'Idempotency-Replayed': str(replayed).lower(), 'Server-Timing': f'app;dur={(time.perf_counter() - started) * 1000:.3f}'}
    if status == 429 or (status == 409 and payload.get('code') == 'IDEMPOTENCY_IN_PROGRESS'):
        headers['Retry-After'] = '1' if status == 409 else str(settings.login_window_seconds)
    return JSONResponse(wire(payload), status_code=status, headers=headers)
