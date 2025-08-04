import { useNavigate } from "react-router-dom";

import "../../../assets/css/components/buttons.css";

type GoBackButtonProps = {
    label?: string;
};

export function GoBackButton({ label = "Retour" }: GoBackButtonProps) {
    const navigate = useNavigate();

    function handleGoBack() {
        navigate(-1); // Go back one step in history
    }

    return (
        <div id="previous" onClick={handleGoBack} className="button">
            <svg
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 16 16"
                preserveAspectRatio="xMidYMid meet"
                data-rnwibasecard--jwli3a-hover="true"
                data-rnwi-handle="nearest"
                className="icon"
            >
                <path
                    fill="inherit"
                    fillRule="evenodd"
                    d="M6.924 3.576a.6.6 0 0 1 0 .848L3.95 7.4H13.5a.6.6 0 1 1 0 1.2H3.949l2.975 2.976a.6.6 0 0 1-.848.848l-4-4a.6.6 0 0 1 0-.848l4-4a.6.6 0 0 1 .848 0Z"
                    clipRule="evenodd"
                />
            </svg>
            <p>{label}</p>
        </div>
    );
}
