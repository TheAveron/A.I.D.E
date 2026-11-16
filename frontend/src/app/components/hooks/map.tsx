import { useEffect, useState } from "react";
import axios from "axios";

import { getErrorMessage } from "../../utils/apierror";
import { dimensionOfFolder } from "../../types/map";
import type { MarkerType, TerritoryType } from "../../types/map";
import type { LineType, StationType } from "../../types/trains";
import { loadUnminedData, type UnminedData } from "../../utils/unmined";

interface State<T> {
    key: string;
    data: T | null;
    error: string | null;
}

/** GET without a login: the map is public, `useApiGet` needs a token. */
function usePublicGet<T>(url: string, errorLabel: string) {
    const [state, setState] = useState<State<T> | null>(null);

    useEffect(() => {
        let cancelled = false;
        axios
            .get<T>(url)
            .then((res) => {
                if (!cancelled)
                    setState({ key: url, data: res.data, error: null });
            })
            .catch((err) => {
                if (!cancelled) {
                    setState({
                        key: url,
                        data: null,
                        error: getErrorMessage(err, errorLabel),
                    });
                }
            });
        return () => {
            cancelled = true;
        };
    }, [url, errorLabel]);

    const current = state && state.key === url ? state : null;
    return {
        data: current?.data ?? null,
        error: current?.error ?? null,
        loading: current === null,
    };
}

/** The tiles' description of an uNmINeD export, and its players. */
export function useUnminedData(folder: string) {
    const [state, setState] = useState<{
        folder: string;
        data: UnminedData | null;
        error: string | null;
    } | null>(null);

    useEffect(() => {
        let cancelled = false;
        loadUnminedData(folder)
            .then((data) => {
                if (!cancelled) setState({ folder, data, error: null });
            })
            .catch(() => {
                if (!cancelled) {
                    setState({
                        folder,
                        data: null,
                        error: "Cette carte n'est pas disponible.",
                    });
                }
            });
        return () => {
            cancelled = true;
        };
    }, [folder]);

    const current = state && state.folder === folder ? state : null;
    return {
        unmined: current?.data ?? null,
        error: current?.error ?? null,
        loading: current === null,
    };
}

/** What the server knows about a map: territories, points, stations, lines. */
export function useMapOverlay(folder: string) {
    const dimension = dimensionOfFolder(folder);
    const territories = usePublicGet<TerritoryType[]>(
        `/map/${encodeURIComponent(folder)}/territories`,
        "Erreur lors du chargement des territoires",
    );
    const markers = usePublicGet<MarkerType[]>(
        `/map/${encodeURIComponent(folder)}/markers`,
        "Erreur lors du chargement des points d'intérêt",
    );
    const stations = usePublicGet<StationType[]>(
        `/stations?limit=200&dimension=${dimension}`,
        "Erreur lors du chargement des gares",
    );
    const lines = usePublicGet<LineType[]>(
        "/lines",
        "Erreur lors du chargement des lignes",
    );

    return {
        territories: territories.data ?? [],
        markers: markers.data ?? [],
        stations: stations.data ?? [],
        lines: lines.data ?? [],
        // A layer that fails to load must not hide the map itself.
        errors: [
            territories.error,
            markers.error,
            stations.error,
            lines.error,
        ].filter((e): e is string => e !== null),
        dimension,
    };
}
