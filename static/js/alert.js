const PrayerAlert = {
    isActive: false,
    currentStage: null, // "masuk" | "countdown" | "jemaah"
    countdownInterval: null,
    countdownSeconds: 0,
    triggeredPrayers: new Set(),

    // Loaded from settings.json via /api/config
    MASUK_DURATION: 30,
    COUNTDOWN_DURATION: 600,
    JEMAAH_DURATION: 600,

    async loadConfig() {
        try {
            const res = await fetch("/api/config");
            if (res.ok) {
                const cfg = await res.json();
                this.MASUK_DURATION = cfg.masuk_duration_seconds || 30;
                this.COUNTDOWN_DURATION = cfg.countdown_duration_seconds || 600;
                this.JEMAAH_DURATION = cfg.jemaah_duration_seconds || 600;
            }
        } catch (e) {
            console.error("Failed to load alert config:", e);
        }
    },

    // Alarm sound using Web Audio API
    audioCtx: null,

    initAudio() {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    },

    playAlarm() {
        if (!this.audioCtx) this.initAudio();

        const ctx = this.audioCtx;
        const now = ctx.currentTime;

        // Play a repeating alarm pattern for ~8 seconds
        for (let i = 0; i < 8; i++) {
            const startTime = now + i * 1.0;

            // First tone (higher)
            const osc1 = ctx.createOscillator();
            const gain1 = ctx.createGain();
            osc1.type = "sine";
            osc1.frequency.value = 880;
            gain1.gain.setValueAtTime(0, startTime);
            gain1.gain.linearRampToValueAtTime(0.3, startTime + 0.05);
            gain1.gain.linearRampToValueAtTime(0, startTime + 0.4);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            osc1.start(startTime);
            osc1.stop(startTime + 0.5);

            // Second tone (lower)
            const osc2 = ctx.createOscillator();
            const gain2 = ctx.createGain();
            osc2.type = "sine";
            osc2.frequency.value = 660;
            gain2.gain.setValueAtTime(0, startTime + 0.5);
            gain2.gain.linearRampToValueAtTime(0.3, startTime + 0.55);
            gain2.gain.linearRampToValueAtTime(0, startTime + 0.9);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            osc2.start(startTime + 0.5);
            osc2.stop(startTime + 1.0);
        }
    },

    start(prayerName, prayerTime) {
        if (this.isActive) return;

        this.isActive = true;
        this.triggeredPrayers.add(prayerName);

        const label = Prayer.prayerLabels[prayerName] || prayerName;

        // Set text for all 3 stages
        document.getElementById("masuk-prayer-name").textContent = label;
        document.getElementById("masuk-prayer-time").textContent = prayerTime || "";
        document.getElementById("countdown-prayer-name").textContent = label.toUpperCase();
        document.getElementById("jemaah-prayer-name").textContent = label;

        // Stage 1: Waktu Solat Telah Masuk
        this.showStage("masuk");
        this.playAlarm();

        setTimeout(() => {
            if (!this.isActive) return;
            // Stage 2: Countdown 10 minutes
            this.showStage("countdown");
            this.startCountdown();
        }, this.MASUK_DURATION * 1000);
    },

    showStage(stage) {
        this.currentStage = stage;

        // Hide all alert pages
        document.querySelectorAll(".alert-page").forEach((el) => {
            el.classList.add("hidden");
        });

        // Show the target stage
        const el = document.getElementById(`alert-${stage}`);
        if (el) el.classList.remove("hidden");
    },

    startCountdown() {
        this.countdownSeconds = this.COUNTDOWN_DURATION;
        this.updateCountdownDisplay();

        this.countdownInterval = setInterval(() => {
            this.countdownSeconds--;
            this.updateCountdownDisplay();

            if (this.countdownSeconds <= 0) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;

                // Stage 3: Solat Berjemaah
                this.showStage("jemaah");

                setTimeout(() => {
                    this.stop();
                }, this.JEMAAH_DURATION * 1000);
            }
        }, 1000);
    },

    updateCountdownDisplay() {
        const mins = Math.floor(this.countdownSeconds / 60);
        const secs = this.countdownSeconds % 60;
        const el = document.getElementById("countdown-timer");
        if (el) {
            el.textContent = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;

            // Turn red in last 60 seconds
            if (this.countdownSeconds <= 60) {
                el.classList.add("urgent");
            } else {
                el.classList.remove("urgent");
            }
        }
    },

    stop() {
        this.isActive = false;
        this.currentStage = null;

        if (this.countdownInterval) {
            clearInterval(this.countdownInterval);
            this.countdownInterval = null;
        }

        // Hide all alert pages
        document.querySelectorAll(".alert-page").forEach((el) => {
            el.classList.add("hidden");
        });
    },

    // Called every 10s — compare clock directly against today's prayer times
    check() {
        if (!Prayer.times) return;

        const now  = new Date();
        const hhmm = `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
        const prayerOrder = ["subuh", "zohor", "asar", "maghrib", "isyak"];

        for (const prayer of prayerOrder) {
            if (Prayer.times[prayer] !== hhmm) continue;
            if (this.triggeredPrayers.has(prayer)) continue;

            // Mark immediately to block repeat fires within the same minute
            this.triggeredPrayers.add(prayer);
            window.location.href = `/waktu_solat?solat=${encodeURIComponent(prayer)}`;
            return;
        }
    },

    // Reset triggered list at midnight
    resetDaily() {
        this.triggeredPrayers.clear();
    },

    // Test mode: trigger alert with short durations
    // Press T in browser to trigger, press Q to skip/stop
    async test(prayer) {
        prayer = prayer || "asar";
        console.log(`[TEST] Triggering alert for: ${prayer}`);

        // Use short durations for testing
        this.MASUK_DURATION = 10;       // 10 seconds instead of 30
        this.COUNTDOWN_DURATION = 30;   // 30 seconds instead of 10 min
        this.JEMAAH_DURATION = 10;      // 10 seconds instead of 30

        // Fetch time from test endpoint
        try {
            const res = await fetch(`/api/test-alert/${prayer}`);
            if (res.ok) {
                const data = await res.json();
                Prayer.times = data.times;
                Prayer.alertActive = data.alert_active;
                Prayer.alertPrayer = data.alert_prayer;
            }
        } catch (e) {
            console.error("Test endpoint failed:", e);
        }

        const prayerTime = Prayer.times ? Prayer.times[prayer] : "";
        this.triggeredPrayers.delete(prayer);
        this.start(prayer, prayerTime);
    },
};

// Keyboard shortcuts for testing
document.addEventListener("keydown", (e) => {
    if (e.key === "t" || e.key === "T") {
        PrayerAlert.test("asar");
    }
    if (e.key === "q" || e.key === "Q") {
        PrayerAlert.stop();
        // Restore normal durations
        PrayerAlert.MASUK_DURATION = 30;
        PrayerAlert.COUNTDOWN_DURATION = 600;
        PrayerAlert.JEMAAH_DURATION = 30;
        console.log("[TEST] Alert stopped, durations restored");
    }
});
