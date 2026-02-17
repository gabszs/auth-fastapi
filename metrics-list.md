# OpenTelemetry Python – Metrics Comparison

This document shows the list of metrics collected before and after enabling the opentelemetry-instrumentation-system-metrics package in an OpenTelemetry automatic instrumentation setup for Python.

The goal is to clearly document which metrics are available:

- Without the system metrics instrumentation
- With the system metrics instrumentation enabled

## Environment

- OpenTelemetry Python (auto-instrumentation)
- ASGI / FastAPI application
- Metrics exported via OTLP
- Containerized environment (Docker)

## Metrics WITHOUT opentelemetry-instrumentation-system-metrics

These metrics are collected by default via:

- Runtime instrumentation (CPython / asyncio)
- Process metrics
- HTTP server instrumentation
- Database instrumentation
- Auto-instrumentation bootstrap

### Available Metrics

```
asyncio_process_created_total
asyncio_process_duration_seconds_bucket
asyncio_process_duration_seconds_count
asyncio_process_duration_seconds_sum
cpython_gc_collected_objects_total
cpython_gc_collections_total
cpython_gc_uncollectable_objects_total
db_client_connections_usage
http_server_active_requests
http_server_duration_milliseconds_bucket
http_server_duration_milliseconds_count
http_server_duration_milliseconds_sum
http_server_request_size_bytes_bucket
http_server_request_size_bytes_count
http_server_request_size_bytes_sum
http_server_response_size_bytes_bucket
http_server_response_size_bytes_count
http_server_response_size_bytes_sum
process_context_switches_total
process_cpu_time_seconds_total
process_cpu_utilization_ratio
process_memory_usage_bytes
process_memory_virtual_bytes
process_open_file_descriptor_count
process_runtime_cpython_context_switches_total
process_runtime_cpython_cpu_time_seconds_total
process_runtime_cpython_cpu_utilization_ratio
process_runtime_cpython_gc_count_bytes_total
process_runtime_cpython_memory_bytes
process_runtime_cpython_thread_count
process_thread_count
target_info
```

## Additional Metrics WITH opentelemetry-instrumentation-system-metrics

After installing:

```bash
pip install opentelemetry-instrumentation-system-metrics
```

The following system-level metrics become available:

```
system_cpu_time_seconds_total
system_cpu_utilization_ratio
system_disk_io_bytes_total
system_disk_operations_total
system_disk_time_seconds_total
system_memory_usage_bytes
system_memory_utilization_ratio
system_network_connections
system_network_dropped_packets_total
system_network_errors_total
system_network_io_bytes_total
system_network_packets_total
system_swap_usage_pages
system_swap_utilization_ratio
system_thread_count
```

## Important Notes

- In containerized environments (e.g., Docker), `system_*` metrics reflect the container namespace, not the host node.
- `process_*` metrics refer only to the Python process.
- Runtime metrics (`cpython_*`, `asyncio_*`) are independent of system metrics and are collected automatically.

## Summary

| Category | Without System Metrics | With System Metrics |
|----------|:----------------------:|:-------------------:|
| Runtime (CPython / asyncio) | ✅ | ✅ |
| Process metrics | ✅ | ✅ |
| HTTP server metrics | ✅ | ✅ |
| DB metrics | ✅ | ✅ |
| System-level metrics | ❌ | ✅ |

This comparison helps clarify exactly what changes when enabling system metrics in OpenTelemetry Python auto-instrumentation.