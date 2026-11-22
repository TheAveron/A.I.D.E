import axios from "axios";
import { useCallback, useState } from "react";

import { getErrorMessage } from "../../utils/apierror";
import { useApiGet } from "../../utils/useapiget";

import type {
    CurrencyLinkRequestType,
    CurrencyType,
} from "../../types/currency";

/** Every currency (name, symbol, factions), to pick one to ask for. */
export function useCurrencies(enabled: boolean) {
    const { data, loading, error, refresh } = useApiGet<CurrencyType[]>(
        enabled ? "/currencies" : null,
        "Impossible de charger les monnaies",
    );
    return { currencies: data ?? [], loading, error, refresh };
}

/** The pending requests and invitations of a currency (for its managers). */
export function useCurrencyLinkRequests(currencyId: number | null) {
    const { data, loading, error, refresh } = useApiGet<
        CurrencyLinkRequestType[]
    >(
        currencyId !== null ? `/currencies/${currencyId}/links` : null,
        "Impossible de charger les demandes de monnaie",
    );
    return { requests: data ?? [], loading, error, refresh };
}

/**
 * A faction's pending requests and the invitations it received (for its
 * holders of manage_funds).
 */
export function useFactionLinkRequests(factionId: string | null) {
    const { data, loading, error, refresh } = useApiGet<
        CurrencyLinkRequestType[]
    >(
        factionId
            ? `/currencies/links/faction/${encodeURIComponent(factionId)}`
            : null,
        "Impossible de charger les demandes de monnaie",
    );
    return { requests: data ?? [], loading, error, refresh };
}

/**
 * Everything that changes who uses a currency. Each action resolves to true
 * when the server accepted it; otherwise `error` holds its message.
 */
export function useCurrencyLinkActions() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const run = useCallback(
        async (call: () => Promise<unknown>): Promise<boolean> => {
            setLoading(true);
            setError(null);
            try {
                await call();
                return true;
            } catch (err) {
                setError(getErrorMessage(err));
                return false;
            } finally {
                setLoading(false);
            }
        },
        [],
    );

    const request = useCallback(
        (currencyId: number) =>
            run(() => axios.post(`/currencies/${currencyId}/links/request`)),
        [run],
    );
    const invite = useCallback(
        (currencyId: number, factionId: number) =>
            run(() =>
                axios.post(`/currencies/${currencyId}/links/invite`, {
                    faction_id: factionId,
                }),
            ),
        [run],
    );
    const accept = useCallback(
        (requestId: number) =>
            run(() => axios.post(`/currencies/links/${requestId}/accept`)),
        [run],
    );
    const refuse = useCallback(
        (requestId: number) =>
            run(() => axios.post(`/currencies/links/${requestId}/refuse`)),
        [run],
    );
    const withdraw = useCallback(
        (requestId: number) =>
            run(() => axios.delete(`/currencies/links/${requestId}`)),
        [run],
    );
    const setIssuer = useCallback(
        (currencyId: number, factionId: number, isIssuer: boolean) =>
            run(() =>
                isIssuer
                    ? axios.put(
                          `/currencies/${currencyId}/factions/${factionId}/issuer`,
                      )
                    : axios.delete(
                          `/currencies/${currencyId}/factions/${factionId}/issuer`,
                      ),
            ),
        [run],
    );
    const removeFaction = useCallback(
        (currencyId: number, factionId: number) =>
            run(() =>
                axios.delete(`/currencies/${currencyId}/factions/${factionId}`),
            ),
        [run],
    );

    return {
        request,
        invite,
        accept,
        refuse,
        withdraw,
        setIssuer,
        removeFaction,
        loading,
        error,
    };
}
