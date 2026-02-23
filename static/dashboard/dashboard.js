let event_chart = null;
document.addEventListener('alpine:init', () => {

    Alpine.store('dashboard', {

        // -----------------------------
        // STATE
        // -----------------------------

        events: [],
        socketBase:null,
        socket: null,
        connected: false,
        reconnectAttempts: 0,
        reconnectTimer: null,

        filters: {
            eventType: "all",
            status: "all",
        },

        searchQuery: "",
        debouncedSearch: "",
        timeWindowMinutes: 10,
        paused: false,
        preferencesKey: "dashboardPreferences",
        selectedEvent: null,
        drawerOpen: false,

        // -----------------------------
        // INIT
        // -----------------------------

        async init() {
            this.loadPreferences();
            const root_event = document.querySelector("[data-events-url]");
            
            this.eventsUrl = root_event.dataset.eventsUrl;
            const root_metric = document.querySelector("[data-metrics-url]");
            this.metricsUrl = root_metric.dataset.metricsUrl;
            await this.loadInitialEvents();
            await this.fetchMetrics();
            this.connect();
        },
        // -----------------------------
        // INITIAL LOAD
        // ----------------------------
        async loadInitialEvents() {
            try {
                const response = await fetch(this.eventsUrl);
                const data = await response.json();
                this.events = data;
            } catch (err) {
                console.error("Failed to load initial events", err);
            }
        },
        async fetchMetrics() {
            if (!this.metricsUrl) return;

            try {
                const response = await fetch(
                `${this.metricsUrl}?window=${this.timeWindowMinutes}`
                );
                console.log(response)

                this.serverMetrics = await response.json();
            } catch (err) {
                console.error("Failed to fetch metrics", err);
            }
        },
        // -----------------------------
        // WEBSOCKET CONNECTION
        // -----------------------------

        connect() {
            console.log("Trying to connect")
            if (this.socket) return;
            const protocol = window.location.protocol === "https:" ? "wss" : "ws";
            const url = `${protocol}://${window.location.host}/ws/events/`;

            this.socket = new WebSocket(url);

            this.socket.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                console.log("WebSocket connected");
            };
            
            this.socket.onmessage = (event) => {
                if (this.paused) return;

                const data = JSON.parse(event.data);
                if (data.type === "metrics_update") {
                    this.serverMetrics = data;
                    return;
                }
                this.events.push(data);
            };

            this.socket.onclose = () => {
                console.warn("WebSocket disconnected");
                this.connected = false;
                this.socket = null;
                this.scheduleReconnect();
            };

            this.socket.onerror = () => {
                this.socket.close();
            };
        },
        updateWindow(){
            console.log("calling update window");
            if(!this.socket) return;        
            console.log("socket present");
            try{
                this.socket.send(JSON.stringify({
                    type:"update_window",
                    window: this.timeWindowMinutes
                }));
            }catch(e){
                console.log(e);
            }
                
            

        },
        get connectionMessage() {
            if (this.connected) return "";

            if (this.reconnectAttempts === 0) {
                return "Connecting to realtime stream...";
            }

            return `Reconnecting... (Attempt ${this.reconnectAttempts})`;
        },
        // -----------------------------
        // AUTO RECONNECT
        // -----------------------------

        scheduleReconnect() {

            if (this.reconnectTimer) return;

            this.reconnectAttempts++;

            const delay = Math.min(1000 * this.reconnectAttempts, 10000);

            this.reconnectTimer = setTimeout(() => {
                this.reconnectTimer = null;
                this.connect();
            }, delay);
        },
        // -----------------------------
        // COMPUTED (FILTER PIPELINE)
        // -----------------------------

        get windowedEvents() {
            const cutoff = Date.now() - this.timeWindowMinutes * 60_000;
            return this.events.filter(e =>
                new Date(e.timestamp).getTime() >= cutoff
            );
        },

        get filteredEvents() {
            return this.windowedEvents.filter(e => {

                if (
                    this.filters.eventType !== "all" &&
                    e.event_type !== this.filters.eventType
                ) return false;

                if (
                    this.filters.status !== "all" &&
                    e.status !== this.filters.status
                ) return false;

                if (this.debouncedSearch) {
                    const text = (
                        e.event_type +
                        " " +
                        (e.source || "") +
                        " " +
                        JSON.stringify(e.payload || {})
                    ).toLowerCase();

                    if (!text.includes(this.debouncedSearch))
                        return false;
                }

                return true;
            });
        },
        formatTime(ts) {
            const d = new Date(ts);
            const day = String(d.getDate()).padStart(2, "0");
            const month = String(d.getMonth() + 1).padStart(2, "0");
            const year = d.getFullYear();

            let hours = d.getHours();
            const minutes = String(d.getMinutes()).padStart(2, "0");

            const ampm = hours >= 12 ? "PM" : "AM";
            hours = hours % 12;
            hours = hours ? hours : 12; // 0 → 12
            hours = String(hours).padStart(2, "0");

            return `${day}-${month}-${year} ${hours}:${minutes} ${ampm}`;
        },
        // -----------------------------
        // METRICS
        // -----------------------------

        get totalEvents() {
            return this.filteredEvents.length;
        },

        get successCount() {
            return this.filteredEvents.filter(e => e.status === "success").length;
        },

        get errorCount() {
            return this.filteredEvents.filter(e => e.status === "error").length;
        },

        get successRate() {
            if (!this.filteredEvents.length) return 0;
            return Math.round((this.successCount / this.filteredEvents.length) * 100);
        },

        get errorRate() {
            if (!this.filteredEvents.length) return 0;
            return Math.round((this.errorCount / this.filteredEvents.length) * 100);
        },

        get eventsPerMinute() {
            if (!this.timeWindowMinutes) return 0;
            return Math.round(this.filteredEvents.length / this.timeWindowMinutes);
        },

        get averageDuration() {
            const events = this.filteredEvents.filter(e => e.duration_ms != null);
            if (!events.length) return 0;

            const sum = events.reduce((acc, e) => acc + e.duration_ms, 0);
            return Math.round(sum / events.length);
        },

        get p95Duration() {
            const durations = this.filteredEvents
                .map(e => e.duration_ms)
                .filter(Boolean)
                .sort((a, b) => a - b);

            if (!durations.length) return 0;
            return durations[Math.floor(durations.length * 0.95)];
        },

        get eventsPerSecond() {
            const cutoff = Date.now() - 10_000;
            const count = this.filteredEvents.filter(e =>
                new Date(e.timestamp).getTime() >= cutoff
            ).length;

            return (count / 10).toFixed(1);
        },
        // -----------------------------
        // SEARCH
        // -----------------------------

        handleSearchInput() {
            clearTimeout(this._searchTimer);
            this._searchTimer = setTimeout(() => {
                this.debouncedSearch = this.searchQuery.toLowerCase();
            }, 250);
        },

        clearSearch() {
            this.searchQuery = "";
            this.debouncedSearch = "";
        },
        // -----------------------------
        // DRAWER
        // -----------------------------

        openEvent(e) {
            this.selectedEvent = e;
            this.drawerOpen = true;
        },

        closeDrawer() {
            this.drawerOpen = false;
        },

        // -----------------------------
        // EXPORT
        // -----------------------------

        exportCSV() {
            const headers = [
                "id",
                "timestamp",
                "event_type",
                "status",
                "duration_ms",
            ];

            const rows = this.filteredEvents.map(e =>
                headers.map(h => `"${e[h] ?? ""}"`).join(",")
            );

            const csv = headers.join(",") + "\n" + rows.join("\n");

            const blob = new Blob([csv], { type: "text/csv" });
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "events.csv";
            a.click();

            URL.revokeObjectURL(url);
        },
        loadPreferences() {
            const saved = localStorage.getItem(this.preferencesKey)
            if (!saved) return;
            try {
                const prefs = JSON.parse(saved);
                console.log(prefs);
                if (prefs.filters) {
                    console.log("a");
                    this.filters = { ...this.filters, ...prefs.filters };
                }
                if (prefs.timeWindowMinutes) {
                    this.timeWindowMinutes = Number(prefs.timeWindowMinutes);
                }
                if (prefs.searchQuery) {
                    console.log("c");
                    this.searchQuery = prefs.searchQuery;
                }
                if (typeof prefs.paused == "boolean") {
                    this.paused = prefs.paused;
                }
            } catch (e) {
                console.log(e);
                console.warn("Failed to load dashboard preferences");
            }
        },
    });

    Alpine.data("chartComponent", () => ({

        initChart() {
            const ctx = document.getElementById("eventsChart");
            if (!ctx) return;

            event_chart = new Chart(ctx, {
                type: "line",
                data: {
                    labels: [],
                    datasets: [
                        {
                            label: "Success / Minute",
                            data: [],
                            borderColor: "#22c55e",
                            borderWidth: 2,
                            tension: 0.3,
                        },
                        {
                            label: "Error / Minute",
                            data: [],
                            borderColor: "#ef4444",
                            borderWidth: 2,
                            tension: 0.3,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    animation: false,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });

            // Watch filtered events from store
            this.$watch(
                () => Alpine.store("dashboard").filteredEvents,
                () => {
                    this.updateChart();
                }
            );

            this.updateChart();
        },

        updateChart() {
            if (!event_chart) return;

            const store = Alpine.store("dashboard");
            const buckets = {};

            store.filteredEvents.forEach(e => {
                const d = new Date(e.timestamp);
                d.setSeconds(0, 0);
                const key = d.toISOString();

                if (!buckets[key]) {
                    buckets[key] = { success: 0, error: 0 };
                }

                if (e.status === "success") {
                    buckets[key].success++;
                } else {
                    buckets[key].error++;
                }
            });

            const labels = Object.keys(buckets).sort().slice(-store.timeWindowMinutes);

            event_chart.data.labels = labels.map(l =>
                new Date(l).toLocaleTimeString()
            );

            event_chart.data.datasets[0].data = labels.map(k => buckets[k].success);
            event_chart.data.datasets[1].data = labels.map(k => buckets[k].error);

            event_chart.update("none");
        }

    }));
    queueMicrotask(() => {
        console.log("Running microtask");
        Alpine.store("dashboard").init();
    });
    Alpine.effect(() => {
        console.log("saving")
        const store = Alpine.store("dashboard");

        // Track dependencies explicitly
        const prefs = {
            filters: store.filters,
            timeWindowMinutes: store.timeWindowMinutes,
            searchQuery: store.searchQuery,
            paused:store.paused
        };

        localStorage.setItem(
            store.preferencesKey,
            JSON.stringify(prefs)
        );
    });

});
