// Gameface loader for the WNX battle scoreboard.
import { MediaContext } from "../../libs/media.js";
import { ModelObserver } from "../../libs/model.js";
import { playSound } from "../../libs/sound.js";

const media = MediaContext();
const model = ModelObserver("UnicumWnxTab");
const style = document.createElement("style");

let running = null;
let loaded = null;

function report(text) {
    if (model.model) {
        model.model.onItemClick({ item: "log", text: String(text).slice(0, 4000) });
    }
}

function load() {
    const current = model.model;
    if (!current || !current.script || current.revision === loaded) {
        return;
    }
    loaded = current.revision;
    if (running) {
        try {
            running.stop();
        } catch (error) {
            report(`WNX Tab: stop failed: ${error}`);
        }
        running = null;
    }
    style.textContent = current.style || "";
    try {
        running = new Function("api", current.script)({ model, media, playSound, report });
    } catch (error) {
        report(`WNX Tab: script failed: ${error} ${error && error.stack ? error.stack : ""}`);
    }
}

engine.whenReady.then(() => {
    document.head.appendChild(style);
    media.subscribe();
    model.onUpdate(load);
    model.subscribe();
    load();
});
