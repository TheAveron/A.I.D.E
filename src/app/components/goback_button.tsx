import { useNavigate } from "react-router-dom";
import previousArrow from "../../assets/images/previous.svg";


type GoBackButtonProps = {
  label?: string;
};

export function GoBackButton({ label = "Retour" }: GoBackButtonProps) {
  const navigate = useNavigate();

  function handleGoBack() {
    navigate(-1); // Go back one step in history
  }

  return (
    <button id="previous" onClick={handleGoBack} className="go-back-button">
      <img src={previousArrow} width="20px" alt="Back arrow" />
      <p>{label}</p>
    </button>
  );
}
