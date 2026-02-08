from datetime import datetime

import pyroscope
from fastapi import Request
from fastapi import Response
from opentelemetry import trace
from opentelemetry.trace import get_current_span
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.settings import settings
# from device_detector import DeviceDetector

tracer = trace.get_tracer(__name__)


class PyroscopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        route = request.scope.get("route")
        template = getattr(route, "path_format", getattr(route, "path", request.url.path))
        method = request.method
        tag = f"{method}:{template}"
        with pyroscope.tag_wrapper({"endpoint": tag}):
            return await call_next(request)


class OtelMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        span = get_current_span()
        start_time = datetime.now()
        trace_id = span.get_span_context().trace_id
        request.state.trace_id = trace_id

        client_address = request.headers.get("cf-connecting-ip", "")
        user_agent_str = request.headers.get("user-agent", "")

        # ua = DeviceDetector(user_agent_str).parse() if user_agent_str else None
        sec_ch_ua_platform = request.headers.get("sec-ch-ua-platform", "")

        # Extrai o body se existir
        request_body = None
        try:
            request_body = await request.json()
        except Exception:
            pass

        event: dict = {
            # Service attributes
            # "service.environment": settings.OTEL_SERVICE_NAMESPACE,
            # "service.owner.name": settings.SERVICE_OWNER_NAME,
            # "service.owner.url": settings.SERVICE_OWNER_URL,
            # "service.owner.contact": settings.SERVICE_OWNER_CONTACT,
            # "service.owner.discord": settings.SERVICE_OWNER_DISCORD,
            # "service.version": settings.SERVICE_VERSION,
            # "service.build.git_hash": settings.COMMIT_HASH,
            # "service.build.git_branch": settings.COMMIT_BRANCH,
            # "service.build.deployment.user": settings.DEPLOYMENT_USER,
            # "service.build.deployment.trigger": settings.DEPLOYMENT_TRIGGER,
            # Client geo attributes (from Cloudflare headers)
            "client.geo.country.iso_code": request.headers.get("cf-ipcountry", ""),
            "client.geo.locality.name": request.headers.get("cf-ipcity", ""),
            "client.geo.location.lat": request.headers.get("cf-iplatitude", ""),
            "client.geo.location.lon": request.headers.get("cf-iplongitude", ""),
            "client.geo.region.iso_code": request.headers.get("cf-region-code", ""),
            "client.geo.postal_code": request.headers.get("cf-postal-code", ""),
            "client.geo.continent.code": request.headers.get("cf-ipcontinent", ""),
            "client.geo.colo": request.headers.get("cf-colo", ""),
            "client.network.asn": request.headers.get("cf-asn", ""),
            "client.network.as.organization": request.headers.get("cf-asorg", ""),
            # User agent attributes
            "user_agent.original": user_agent_str,
            # "user_agent.device.model": ua.device_model() if ua else None,
            # "user_agent.device.type": ua.device_type() if ua else None,
            # "user_agent.device.vendor": ua.device_brand() if ua else None,
            # "user_agent.os": ua.os_name() if ua else None,
            # "user_agent.os.version": ua.os_version() if ua else None,
            # "user_agent.browser": ua.client_name() if ua else None,
            # "user_agent.browser_version": ua.client_version() if ua else None,
            # "user_agent.engine": ua.engine() if ua else None,
            # Browser attributes (Client Hints)
            "browser.brands": request.headers.get("sec-ch-ua", ""),
            "browser.mobile": request.headers.get("sec-ch-ua-mobile", "") == "?1",
            "browser.platform": sec_ch_ua_platform.replace('"', "") if sec_ch_ua_platform else None,
            # Request attributes
            "http.request.id": request.headers.get("cf-ray", ""),
            "client.address": client_address,
            "http.request.body": request_body,
            "test.body": {"hello": "world", "number": 123, "list": [1, 2, 3], "dict": {"key": "value"}},
            # **({"http.request.body": request_body} if request_body is not None else {}),
        }

        request.state.wide_event = event

        response = await call_next(request)
        status_code = response.status_code
        is_error = status_code >= 400
        is_rate_limit = status_code == 429

        event["http.response.status_code"] = status_code
        event["http.duration_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        event["http.ratelimit.triggered"] = is_rate_limit
        event["http.outcome"] = "error" if is_error else "success"
        span.set_attributes(event)
        response.headers["otel-trace-id"] = format(trace_id, "032x")
        return response
