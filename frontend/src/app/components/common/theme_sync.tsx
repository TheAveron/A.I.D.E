import { usePreferences } from "../../hooks/users/preferences";

/** Mounted once for logged-in pages: shows the theme saved on the account. */
export default function ThemeSync() {
    usePreferences();
    return null;
}
