import { useOffer } from "../hooks/offers";

export function Offername({ offerId }: { offerId: number }) {
    const { offer } = useOffer(offerId);

    return <>{offer?.item_description}</>;
}
