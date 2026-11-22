import { useCallback, useEffect, useMemo, useRef } from "react";
import axios from "axios";

import { useAuth } from "../../utils/authcontext";
import { useApiGet } from "../../utils/useapiget";
import type { MapDisplay, PreferencesType } from "../../types/preferences";

const LOCAL_KEY = "aide.map.display";
// Clicks in a row on the legend make one request
const SAVE_DELAY_MS = 1000;

function readLocal(): MapDisplay | null {
    try {
        const raw = localStorage.getItem(LOCAL_KEY);
        return raw ? (JSON.parse(raw) as MapDisplay) : null;
    } catch {
        return null; // No storage, or something unreadable: everything shown
    }
}

function writeLocal(display: MapDisplay) {
    try {
        localStorage.setItem(LOCAL_KEY, JSON.stringify(display));
    } catch {
        // Not remembered in this browser: nothing to tell the viewer
    }
}

/**
 * What the map showed when the person left it. Saved on the account when
 * logged in (it follows them from one browser to another), in the browser
 * otherwise. Silent: a save that fails is simply not kept.
 *
 * `ready` turns true once `initial` is known; `save` is called on each change.
 */
export function useSavedMapDisplay() {
    const { token } = useAuth();
    const prefs = useApiGet<PreferencesType>(
        token ? "/preferences" : null,
        "Préférences de la carte",
    );
    const ready = !token || !prefs.loading;
    const fromAccount = prefs.data?.map_display ?? null;
    const initial = useMemo(
        () => (token ? (fromAccount ?? readLocal()) : readLocal()),
        [token, fromAccount],
    );

    const lastSaved = useRef<string | null>(null);
    const pending = useRef<{ timer: number; body: MapDisplay } | null>(null);

    const send = useCallback((body: MapDisplay) => {
        axios.put("/preferences", { map_display: body }).catch(() => {
            lastSaved.current = null; // try again on the next change
        });
    }, []);

    const save = useCallback(
        (display: MapDisplay) => {
            const json = JSON.stringify(display);
            if (lastSaved.current === null) {
                lastSaved.current = JSON.stringify(initial);
            }
            if (json === lastSaved.current) return;
            lastSaved.current = json;
            writeLocal(display);
            if (!token) return;
            if (pending.current) window.clearTimeout(pending.current.timer);
            pending.current = {
                body: display,
                timer: window.setTimeout(() => {
                    pending.current = null;
                    send(display);
                }, SAVE_DELAY_MS),
            };
        },
        [token, initial, send],
    );

    // Leaving the page before the delay: the last change is still sent
    useEffect(
        () => () => {
            if (pending.current) {
                window.clearTimeout(pending.current.timer);
                send(pending.current.body);
                pending.current = null;
            }
        },
        [send],
    );

    return { ready, initial, save };
}
