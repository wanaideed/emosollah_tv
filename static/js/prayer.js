const Prayer = {
    times: null,
    nextPrayer: null,
    nextTime: null,
    alertActive: false,
    alertPrayer: null,

    prayerOrder: ["subuh", "syuruk", "zohor", "asar", "maghrib", "isyak"],
    prayerLabels: {
        subuh: "Subuh",
        syuruk: "Syuruk",
        zohor: "Zohor",
        asar: "Asar",
        maghrib: "Maghrib",
        isyak: "Isyak",
    },

    async fetch() {
        try {
            const res = await fetch("/api/prayer-times");
            if (!res.ok) return;

            const data = await res.json();
            this.times = data.times;
            this.nextPrayer = data.next_prayer;
            this.nextTime = data.next_time;
            this.alertActive = data.alert_active;
            this.alertPrayer = data.alert_prayer;

            this.render();
        } catch (e) {
            console.error("Failed to fetch prayer times:", e);
        }
    },

    hijriMonths: [
        "Muharram", "Safar", "Rabiulawal", "Rabiulakhir",
        "Jamadilawal", "Jamadilakhir", "Rejab", "Syaaban",
        "Ramadan", "Syawal", "Zulkaedah", "Zulhijjah",
    ],

    formatHijri(hijriStr) {
        // hijriStr format: "1447-10-12" → "12 Syawal 1447H"
        if (!hijriStr) return "";
        const parts = hijriStr.split("-");
        if (parts.length !== 3) return hijriStr;
        const year = parts[0];
        const month = parseInt(parts[1], 10);
        const day = parseInt(parts[2], 10);
        const monthName = this.hijriMonths[month - 1] || "";
        return `${day} ${monthName} ${year}H`;
    },

    render() {
        if (!this.times) return;

        const now = this.getCurrentTime();

        // Render hijri date
        const hijriEl = document.getElementById("date-hijri");
        if (hijriEl && this.times.hijri) {
            hijriEl.textContent = this.formatHijri(this.times.hijri);
        }

        this.prayerOrder.forEach((prayer) => {
            const timeEl = document.getElementById(`time-${prayer}`);
            const cardEl = document.getElementById(`card-${prayer}`);
            if (!timeEl || !cardEl) return;

            timeEl.textContent = this.times[prayer] || "--:--";

            cardEl.classList.remove("active-prayer");
        });
    },

    updateCountdown() {
        if (!this.nextTime) return;

        const now = new Date();
        const [h, m] = this.nextTime.split(":").map(Number);
        const target = new Date();
        target.setHours(h, m, 0, 0);

        // If target is in the past, it means next prayer is tomorrow
        if (target <= now) {
            target.setDate(target.getDate() + 1);
        }

        const diff = Math.max(0, Math.floor((target - now) / 1000));
        const hours = Math.floor(diff / 3600);
        const mins = Math.floor((diff % 3600) / 60);
        const secs = diff % 60;

        const countdownEl = document.getElementById("next-prayer-countdown");
        if (countdownEl) {
            countdownEl.textContent =
                `${String(hours).padStart(2, "0")}:${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
        }
    },

    getCurrentTime() {
        const now = new Date();
        return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
    },

    updateClock() {
        const now = new Date();
        const clockEl = document.getElementById("clock");
        if (clockEl) {
            clockEl.textContent = now.toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
                hour12: true,
            });
        }

        const dateEl = document.getElementById("date-gregorian");
        if (dateEl) {
            dateEl.textContent = now.toLocaleDateString("ms-MY", {
                weekday: "long",
                year: "numeric",
                month: "long",
                day: "numeric",
            });
        }
    },
};
