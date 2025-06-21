function Contribution() {
    return (
        <section
            className="text-section contribution"
            style={{ textAlign: "justify" }}
        >
            <h1>Contribuer au site</h1>
            <p>
                Afin de pouvoir ajouter de nouvelles cartes au site, vous devez
                pour cela les générer avec unmined. Il y a quelques informations
                supplémentaires qui seront indiqués ultérieuerement sur la
                configuration nécessaire d'unmined pour conserver une cohérence.
            </p>
            <p>
                Une fois la carte générée, vous pouvez l'ajouter dans le dossier{" "}
                <code>public/maps</code> du projet. Il est important de
                respecter la structure de nommage suivante :{" "}
                <code>nom_de_la_map/</code>.
            </p>
            <p>
                Vous devez ensuite vous rendre dans le fichier{" "}
                <code>src/app/pages/mapslist.tsx</code> et ajouter un nouvel
                objet dans les variables suivantes :
                <ul>
                    <li>
                        mapFolders : un tableau contenant les noms des dossiers
                        des cartes (doit correspondre à la structure de nommage
                        dans <code>public/maps</code>)
                    </li>
                    <li>
                        getLabelFromFolder : une fonction prenant en entrée le
                        nom d'un dossier et retournant le label à afficher pour
                        ce dossier
                    </li>
                </ul>
            </p>
        </section>
    );
}

export default Contribution;
