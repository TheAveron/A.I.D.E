import { Link } from "react-router";

function Contribution() {
    return (
        <section
            className="text-section contribution"
            style={{ textAlign: "justify" }}
        >
            <h1>Contribuer au site</h1>
            <p>
                Le code du site est ouvert : tout le monde peut proposer une
                carte, une page de documentation ou une correction. Le projet
                est hébergé sur{" "}
                <a
                    href="https://github.com/TheAveron/A.I.D.E"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    GitHub
                </a>
                .
            </p>

            <h2>Proposer une modification</h2>
            <ol>
                <li>
                    Créez une branche à partir de <code>main</code> (ou un fork
                    du dépôt si vous n&apos;y avez pas accès en écriture).
                </li>
                <li>Faites vos modifications sur cette branche.</li>
                <li>
                    Si vous avez touché au code, lancez <code>pytest</code> dans{" "}
                    <code>backend/</code> et <code>npm run lint</code> dans{" "}
                    <code>frontend/</code>.
                </li>
                <li>
                    Ouvrez une pull request vers <code>main</code> en expliquant
                    ce qu&apos;elle apporte.
                </li>
            </ol>
            <p>
                Une simple page de documentation ne demande aucune
                connaissance en programmation : seuls des fichiers Markdown
                sont à ajouter.
            </p>

            <h2>Ajout d&apos;une nouvelle map</h2>
            <p>
                Afin de pouvoir ajouter de nouvelles cartes au site, vous devez
                pour cela les générer avec unmined. Il y a quelques informations
                supplémentaires qui seront indiquées ultérieurement sur la
                configuration nécessaire d&apos;unmined pour conserver une
                cohérence.
            </p>
            <p>
                Une fois la carte générée, vous pouvez l&apos;ajouter dans le
                dossier <code>backend/documents/maps</code> du projet. Il est
                important de placer ensuite les fichiers et dossiers générés par
                Unmined directement à la racine d&apos;un nouveau dossier nommé
                comme tel : <code>nom_de_la_map/</code>. Il faut préciser devant
                une lettre, O, E ou N, en fonction de si la map correspond à
                l&apos;overworld, l&apos;end ou le nether.
            </p>
            <p>
                Vous devez ensuite vous rendre dans le fichier{" "}
                <code>src/app/utils/maps.ts</code> et ajouter le nom du dossier
                dans l&apos;objet suivant :
            </p>
            <ul>
                <li>
                    MAP_LABELS : associe le nom du dossier de la carte (il doit
                    correspondre exactement au nom donné au dossier créé dans{" "}
                    <code>backend/documents/maps</code>) au label affiché pour
                    cette carte.
                </li>
            </ul>

            <h2>Ajout d&apos;un nouveau fichier dans la documentation</h2>
            <p>
                La documentation d&apos;Age of Steam est faite de fichiers
                Markdown rangés dans <code>backend/documents/AgeOfSteam/</code>.
                Chaque fichier devient une page, accessible à l&apos;adresse{" "}
                <code>/documentation/AgeOfSteam/nom_du_fichier</code>.
            </p>

            <h3>1. Créer le fichier</h3>
            <p>
                Le nom du fichier sert d&apos;adresse à la page : il doit
                s&apos;écrire en <strong>minuscules</strong>,{" "}
                <strong>sans accents, sans chiffres ni ponctuation</strong>, les
                mots étant séparés par des <code>_</code> (par exemple{" "}
                <code>normes_ferroviaires.md</code>). Un nom qui ne respecte pas
                ces règles ne pourra pas être ouvert.
            </p>
            <p>
                La première ligne du fichier est le titre de la page, précédé
                de <code># </code> :
            </p>
            <pre>
                <code>{`# Titre de la page

Le texte de la page...

## Une section

- une liste
- [un lien vers une autre page](doc://nom_de_l_autre_page)`}</code>
            </pre>

            <h3>2. Liens et images</h3>
            <ul>
                <li>
                    Lien vers une autre page de la documentation :{" "}
                    <code>[texte](doc://nom_du_fichier)</code>, sans{" "}
                    <code>.md</code>.
                </li>
                <li>
                    Lien vers une page du site : <code>[texte](/network)</code>
                    ; vers un site extérieur : <code>[texte](https://…)</code>.
                </li>
                <li>
                    Lien vers une section de la même page :{" "}
                    <code>[texte](#titre-de-la-section)</code>.
                </li>
                <li>
                    Les images et schémas se placent dans{" "}
                    <code>frontend/public/images/docs/</code> (un sous-dossier
                    par sujet) et s&apos;affichent avec{" "}
                    <code>![description](/images/docs/sujet/image.svg)</code>.
                    Préférez le SVG pour les schémas : il reste net à toutes les
                    tailles. Donnez-leur un fond clair, pour qu&apos;ils restent
                    lisibles dans le thème clair comme dans le sombre.
                </li>
            </ul>

            <h3>3. Référencer la page</h3>
            <p>
                Pour que la page apparaisse dans le sommaire de la{" "}
                <Link to="/documentation">documentation</Link>, ajoutez un lien
                vers elle dans{" "}
                <code>
                    frontend/src/app/pages/documentation/documentation.tsx
                </code>
                . Vous pouvez aussi simplement la lier depuis une page
                existante.
            </p>

            <h3>Documents des factions</h3>
            <p>
                Les documents propres à une faction (lois, chartes, annonces…)
                ne passent pas par GitHub : les membres qui en ont la permission
                les écrivent directement depuis la page de leur faction, avec
                l&apos;éditeur intégré.
            </p>
        </section>
    );
}

export default Contribution;
