const Events = {
    images: [],
    currentIndex: 0,

    async fetch() {
        try {
            const res = await fetch("/api/events");
            if (!res.ok) return;

            const data = await res.json();
            this.images = data.images || [];
            this.currentIndex = 0;
        } catch (e) {
            console.error("Failed to fetch events:", e);
        }
    },

    hasImages() {
        return this.images.length > 0;
    },

    showCurrent() {
        if (!this.hasImages()) return;

        const imgEl = document.getElementById("event-image");
        if (imgEl) {
            imgEl.src = this.images[this.currentIndex];
        }
    },

    advance() {
        if (!this.hasImages()) return;
        this.currentIndex = (this.currentIndex + 1) % this.images.length;
        this.showCurrent();
    },
};
