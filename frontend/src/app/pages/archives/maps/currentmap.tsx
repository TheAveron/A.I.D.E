import ServerPage from "../server";
import { CURRENT_MAP_FOLDER } from "../../../utils/maps";

function ActualMap() {
    return ServerPage(CURRENT_MAP_FOLDER);
}

export default ActualMap;
