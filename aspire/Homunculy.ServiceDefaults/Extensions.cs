/*
 * Homunculy Service Defaults (for ASP.NET Core Web Apps)
 * ======================================================
 * 
 * What is Service Defaults?
 * -------------------------
 * A shared configuration project that provides consistent Aspire integration:
 * 
 * 1. SERVICE DISCOVERY
 *    - Resolve "https+http://service-name" to actual URLs
 *    - Aspire injects correct endpoints automatically
 *    - Works with containers, projects, and external services
 * 
 * 2. RESILIENCE (via Polly)
 *    - Retry policies with exponential backoff
 *    - Circuit breakers to prevent cascade failures
 *    - Timeout handling for HTTP calls
 * 
 * 3. OPENTELEMETRY
 *    - Distributed tracing across services
 *    - Metrics (request rates, latencies, errors)
 *    - Structured logs to Aspire Dashboard
 * 
 * 4. HEALTH CHECKS
 *    - /health - Overall health
 *    - /alive - Liveness probe (is the service running?)
 *    - /ready - Readiness probe (is it ready to serve traffic?)
 * 
 * Why separate from MAUI Service Defaults?
 * ----------------------------------------
 * - This uses IHostApplicationBuilder + WebApplication
 * - Includes ASP.NET Core instrumentation
 * - Has HTTP endpoints for health checks
 * - MAUI apps use MauiAppBuilder and don't expose HTTP endpoints
 * 
 * Usage in Program.cs:
 * --------------------
 *   var builder = WebApplication.CreateBuilder(args);
 *   builder.AddServiceDefaults();  // <-- Add this
 *   
 *   var app = builder.Build();
 *   app.MapDefaultEndpoints();     // <-- And this
 *   app.Run();
 */

using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Diagnostics.HealthChecks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Diagnostics.HealthChecks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using OpenTelemetry;
using OpenTelemetry.Metrics;
using OpenTelemetry.Trace;

namespace Microsoft.Extensions.Hosting;

/// <summary>
/// Extension methods for configuring Aspire service defaults.
/// </summary>
public static class Extensions
{
    /// <summary>
    /// Adds service defaults for Aspire applications.
    /// </summary>
    public static IHostApplicationBuilder AddServiceDefaults(this IHostApplicationBuilder builder)
    {
        builder.ConfigureOpenTelemetry();
        builder.AddDefaultHealthChecks();
        builder.Services.AddServiceDiscovery();
        builder.Services.ConfigureHttpClientDefaults(http =>
        {
            http.AddStandardResilienceHandler();
            http.AddServiceDiscovery();
        });

        return builder;
    }

    /// <summary>
    /// Configures OpenTelemetry for metrics, tracing, and logging.
    /// </summary>
    public static IHostApplicationBuilder ConfigureOpenTelemetry(this IHostApplicationBuilder builder)
    {
        builder.Logging.AddOpenTelemetry(logging =>
        {
            logging.IncludeFormattedMessage = true;
            logging.IncludeScopes = true;
        });

        builder.Services.AddOpenTelemetry()
            .WithMetrics(metrics =>
            {
                metrics.AddAspNetCoreInstrumentation()
                    .AddHttpClientInstrumentation()
                    .AddRuntimeInstrumentation();
            })
            .WithTracing(tracing =>
            {
                tracing.AddAspNetCoreInstrumentation()
                    .AddHttpClientInstrumentation();
            });

        builder.AddOpenTelemetryExporters();

        return builder;
    }

    private static IHostApplicationBuilder AddOpenTelemetryExporters(this IHostApplicationBuilder builder)
    {
        var useOtlpExporter = !string.IsNullOrWhiteSpace(builder.Configuration["OTEL_EXPORTER_OTLP_ENDPOINT"]);

        if (useOtlpExporter)
        {
            builder.Services.AddOpenTelemetry().UseOtlpExporter();
        }

        return builder;
    }

    /// <summary>
    /// Adds default health checks.
    /// </summary>
    public static IHostApplicationBuilder AddDefaultHealthChecks(this IHostApplicationBuilder builder)
    {
        builder.Services.AddHealthChecks()
            .AddCheck("self", () => HealthCheckResult.Healthy(), ["live"]);

        return builder;
    }

    /// <summary>
    /// Maps health check endpoints.
    /// </summary>
    public static WebApplication MapDefaultEndpoints(this WebApplication app)
    {
        // Adding health checks endpoints
        // Kubernetes uses liveness and readiness probes
        // - Liveness: Is the service running?
        // - Readiness: Is the service ready to receive traffic?

        app.MapHealthChecks("/health");

        app.MapHealthChecks("/alive", new HealthCheckOptions
        {
            Predicate = r => r.Tags.Contains("live")
        });

        app.MapHealthChecks("/ready", new HealthCheckOptions
        {
            Predicate = r => !r.Tags.Contains("live")
        });

        return app;
    }
}
