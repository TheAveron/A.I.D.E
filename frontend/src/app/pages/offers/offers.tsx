import OfferList from "../../components/offers/offerslist";

function Offers() {
    return (
        <div className="offer-box">
            <OfferList offersPerPage={20} />
        </div>
    );
}

export default Offers;
