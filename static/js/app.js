const App = {
    rotationSeconds: 30,
    enableEventRotation: true,
    currentPage: "prayer", // "prayer" or "event"
    rotationTimer: null,

    async init() {
        // Fetch config
        try {
            const res = await fetch("/api/config");
            if (res.ok) {
                const cfg = await res.json();
                this.rotationSeconds = cfg.rotation_seconds || 30;
                this.enableEventRotation = cfg.enable_event_rotation !== false;
            }
        } catch (e) {
            console.error("Failed to load config:", e);
        }

        // Load alert config
        await PrayerAlert.loadConfig();

        // Initial data load
        await Prayer.fetch();
        await Events.fetch();

        // Update clock every second
        setInterval(() => {
            Prayer.updateClock();
        }, 1000);

        // Refresh prayer data every 5 minutes (to update next prayer / alert)
        setInterval(() => Prayer.fetch(), 5 * 60 * 1000);

        // Refresh event images every 10 minutes
        setInterval(() => Events.fetch(), 10 * 60 * 1000);

        // Check for prayer alert every 10 seconds
        setInterval(() => PrayerAlert.check(), 10 * 1000);

        // Reset triggered prayers at midnight
        setInterval(() => {
            const now = new Date();
            if (now.getHours() === 0 && now.getMinutes() === 0) {
                PrayerAlert.resetDaily();
            }
        }, 60 * 1000);

        // Start page rotation
        this.showPage("prayer");
        this.startRotation();

        // Initial clock render
        Prayer.updateClock();
    },

    showPage(page) {
        const eventImg = document.getElementById("event-image");

        if (page === "prayer") {
            if (eventImg) eventImg.style.display = "none";
            this.currentPage = "prayer";
        } else if (page === "event") {
            Events.showCurrent();
            if (eventImg) eventImg.style.display = "block";
            this.currentPage = "event";
        }
    },

    startRotation() {
        if (!this.enableEventRotation) return;
        if (this.rotationTimer) clearInterval(this.rotationTimer);

        this.rotationTimer = setInterval(() => {
            // Don't rotate during any alert stage
            if (PrayerAlert.isActive) return;

            if (this.currentPage === "prayer") {
                if (Events.hasImages()) {
                    this.showPage("event");
                }
            } else {
                Events.advance();
                if (Events.currentIndex === 0) {
                    this.showPage("prayer");
                }
            }
        }, this.rotationSeconds * 1000);
    },
};

// Start when DOM is ready
document.addEventListener("DOMContentLoaded", () => App.init());
