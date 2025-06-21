/* eslint-disable @typescript-eslint/no-var-requires */
/**
 * Map.tsx
 *
 * This component renders an iframe view of a specific map page in the Cube Crusader application.
 * It uses a loader to receive the `mapname` route param and conditionally shows the iframe after
 * a user interaction. Legacy DOM manipulation is removed in favor of React state and effects.
 */

import { useParams } from "react-router";
import PageGenerator from "../../components/pagegen";

function Map() {
    const { page } = useParams();
    console.log(page);

    return PageGenerator(page ?? "", false);
}

export default Map;
