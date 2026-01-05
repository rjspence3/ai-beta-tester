"""Tools for the Speedrunner personality."""

class SpeedTools:
    @staticmethod
    def get_latency_profiler_js() -> str:
        """Return JS snippet for latency profiling."""
        return """
// HELPER: Interaction Latency Profiler
(function() {
    new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
            if (entry.interactionId > 0) {
                 console.log(`[Interaction] ${entry.name}: ${entry.duration}ms`);
            }
        }
    }).observe({ type: 'event', buffered: true, durationThreshold: 0 });
    return "Latency Profiler Attached. Check console for [Interaction] logs.";
})();
"""
