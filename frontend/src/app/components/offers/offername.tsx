import { useOffer } from "../../hooks/offers/offers";

export function Offername({ offerId }: { offerId: number }) {
    const { offer } = useOffer(offerId);

    return <>{offer?.item_description}</>;
}
