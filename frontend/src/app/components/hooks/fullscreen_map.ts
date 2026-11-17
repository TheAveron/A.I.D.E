import { useEffect } from "react";

/**
 * Map pages take the whole screen: while one is displayed the header is
 * folded away, the footer hidden and the back button / <main> moved up. All
 * of it is given back when the page is left.
 *
 * Same principle as before: inline styles, which win over the stylesheet
 * (layout/header.css also reacts to `height: 0`). On cleanup they are simply
 * removed, so the stylesheet applies again - nothing to keep in sync.
 *
 * Call it from any page that shows a map (iframe of the archives, native
 * viewer of the current map). `enabled` lets a page keep its header when
 * there is nothing to display (unknown map...).
 */
export function useFullscreenMap(enabled = true) {
    useEffect(() => {
        if (!enabled) return;

        const header = document.getElementById("header");
        const footer = document.querySelector("footer");
        const back = document.getElementById("previous");
        const main = document.getElementById("main");
        const title = document.getElementById("map-title");

        title?.classList.remove("column-layout");
        if (footer instanceof HTMLElement) footer.style.display = "none";
        if (header) {
            header.style.height = "0vh";
            header.style.minHeight = "0";
            header.style.paddingTop = "0";
            header.style.paddingBottom = "0";
            header.style.borderBottomWidth = "0";
        }
        if (back) {
            back.style.marginTop = "0";
            back.style.top = "unset";
        }
        if (main) main.style.marginTop = "0";

        return () => {
            if (footer instanceof HTMLElement) footer.style.display = "";
            if (header) {
                header.style.height = "";
                header.style.minHeight = "";
                header.style.paddingTop = "";
                header.style.paddingBottom = "";
                header.style.borderBottomWidth = "";
            }
            if (back) {
                back.style.marginTop = "";
                back.style.top = "";
            }
            if (main) main.style.marginTop = "";
            title?.classList.add("column-layout");
        };
    }, [enabled]);
}
