function Contribution() {
    return (
        <section
            className="text-section contribution"
            style={{ textAlign: "justify" }}
        >
            <h1>Contribuer au site</h1>

            <h2>Ajout d'une nouvelle map</h2>
            <p>
                Afin de pouvoir ajouter de nouvelles cartes au site, vous devez
                pour cela les générer avec unmined. Il y a quelques informations
                supplémentaires qui seront indiqués ultérieuerement sur la
                configuration nécessaire d'unmined pour conserver une cohérence.
            </p>
            <p>
                Une fois la carte générée, vous pouvez l'ajouter dans le dossier{" "}
                <code>backend/documents/maps</code> du projet. Il est important
                de placer ensuite les fichiers et dossiers générés par Unmined
                directement à la racine d'un nouveau dossier nommé comme tel:{" "}
                <code>nom_de_la_map/</code>. Il faut préciser devant une lettre,
                O, E ou N, en fonction de si la map correspond à l'overworld,
                l'end ou le nether.
            </p>
            <p>
                Vous devez ensuite vous rendre dans le fichier{" "}
                <code>src/app/pages/mapslist.tsx</code> et ajouter un nouvel
                objet dans les variables suivantes :
            </p>
            <ul>
                <li>
                    mapFolders : un tableau contenant les noms des dossiers des
                    cartes (doit correspondre exactement au nom donné au dossier
                    que vous avez créé dans <code>backend/documents/maps</code>)
                </li>
                <li>
                    getLabelFromFolder : une fonction prenant en entrée le nom
                    d'un dossier et retournant le label à afficher pour ce
                    dossier.
                </li>
            </ul>

            <h2>Ajout d'un nouveau fichier dans la documentation</h2>
        </section>
    );
}

export default Contribution;
