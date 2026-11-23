# Normes ferroviaires

Le réseau d'Age of Steam est construit par de nombreux joueurs. Pour que deux lignes construites séparément puissent se raccorder, et que les trains y circulent sans se percuter ni se bloquer, toutes les voies du réseau suivent les normes ci-dessous.

Ces normes s'appliquent à toute nouvelle construction raccordée au réseau. Une voie privée, isolée du reste (dans une usine par exemple), peut s'en écarter.

**Sommaire**

- [Légende des schémas](#légende-des-schémas)
- [Principes généraux](#principes-généraux)
- [Gabarit d'une ligne](#gabarit-dune-ligne)
- [Tunnels](#tunnels)
- [Courbes](#courbes)
- [Signalisation](#signalisation)
- [Intersection en T](#intersection-en-t)
- [Gare : quai le long de la ligne](#gare--quai-le-long-de-la-ligne)
- [Mode terminus : la raquette](#mode-terminus--la-raquette)

## Légende des schémas

Les vues de dessus sont tracées sur une grille où **une case vaut un bloc**. Les voies passent au centre des blocs ; les deux voies d'une ligne sont espacées de **6 blocs** (d'axe en axe). Tous les schémas utilisent les mêmes symboles :

| Symbole | Signification |
| --- | --- |
| Chevron **orange** | Sens de circulation de la voie |
| Deux chevrons **orange** opposés | Voie à double sens (section banalisée) |
| Chevron **rouge** simple | Signal simple, placé dans le sens qu'il protège |
| Double chevron **rouge** | Signal chaîné, placé dans le sens qu'il protège |
| Trait noir sur traverses | Voie, tracée au centre des blocs |
| Cadre rouge en pointillés | Zone d'aiguillages ou de croisements |
| Fond orangé | Section banalisée (voies à double sens) |
| Bande bleue | Couloir de voie (3 blocs) |
| Bande jaune | Passage piéton (1 bloc) |
| Bande hachurée beige | Buffer (1 bloc) |
| Rectangle hachuré gris | Quai |
| Pointillé gris terminé par une flèche | Rayon d'un virage, depuis son centre |
| Flèche grise à deux pointes | Cote, en blocs |
| Case de la grille | 1 bloc ; un trait plus foncé tous les 5 blocs |

Un signal se pose toujours **à droite de la voie** dans le sens de la marche, comme le voit le conducteur.

## Principes généraux

- Une ligne principale est **à double voie** : une voie par sens.
- La circulation se fait **à droite**. Sur un plan orienté vers le nord, un train qui part vers le nord roule sur la voie de droite (la plus à l'est).
- Chaque voie n'est parcourue **que dans un seul sens**. Seules certaines sections courtes, dans les gares, sont à double sens (voir [Gare : quai le long de la ligne](#gare--quai-le-long-de-la-ligne)).
- Toute entrée dans une zone d'aiguillages est protégée par un **signal chaîné**, toute sortie par un **signal simple** (voir [Signalisation](#signalisation)).

## Gabarit d'une ligne

![Coupe d'une ligne à double voie : 1 bloc de buffer, 3 blocs de voie, 3 blocs de dégagement avec le passage piéton au centre, 3 blocs de voie, 1 bloc de buffer](/images/docs/ferroviaire/gabarit.svg)

Une ligne à double voie occupe **11 blocs de large**, répartis ainsi :

| Largeur | Zone | Rôle |
| --- | --- | --- |
| 1 bloc | Buffer | Marge de sécurité contre la paroi ou le décor. Rien n'y est construit. |
| 3 blocs | Voie | Le rail est posé sur le bloc central. |
| 3 blocs | Dégagement | Seul le **bloc central** sert de passage piéton. |
| 3 blocs | Voie | Le rail est posé sur le bloc central. |
| 1 bloc | Buffer | Marge de sécurité. |

Les trains font 3 blocs de large mais **débordent légèrement** de leur couloir. Les blocs du dégagement qui touchent les voies sont donc dangereux : on ne marche **que sur le bloc central**.

Aucun élément de décor (poteau, lampe, pilier, panneau) ne doit être placé dans les couloirs de voie ni sur les blocs du dégagement voisins des voies.

## Tunnels

![Coupe d'un tunnel : sol de 11 blocs, plafond de 9 blocs, hauteur de 6 ou 7 blocs, angles supérieurs coupés de 1 × 1 bloc](/images/docs/ferroviaire/tunnel.svg)

Un tunnel reprend exactement le gabarit de la ligne :

- **largeur au sol : 11 blocs**, pour garder les buffers, les deux voies et le dégagement ;
- **hauteur : 6 ou 7 blocs** sous plafond ;
- les deux **angles du plafond sont coupés** d'un bloc sur un bloc, ce qui laisse un **plafond de 9 blocs** de large.

Les angles coupés allègent la silhouette du tunnel sans gêner les trains, qui ne montent pas jusque-là au niveau des buffers.

## Courbes

Create refuse de poser une courbe trop serrée. Les dimensions des schémas reposent sur ces limites, arrondies pour qu'une courbe passe à coup sûr :

Pour un virage, Create mesure la distance entre chaque extrémité de la courbe et l'**angle**, c'est-à-dire le point où se croiseraient les deux voies droites prolongées. Pour un virage à 90°, cette distance est aussi le rayon du virage.

| Courbe | Limite de Create | Norme du réseau |
| --- | --- | --- |
| Virage à 90° | environ 7 blocs jusqu'à l'angle | **8 blocs** (rayon de 8) |
| Virage à 45° | environ 3,25 blocs jusqu'à l'angle | **4 blocs** |
| Courbe en S (passage sur une voie parallèle décalée de _d_ blocs) | longueur d'au moins 2 × _d_ (et 3 au minimum), uniquement à plat | **longueur de 2 × _d_ + 2** |

Une communication entre les deux voies d'une ligne (décalage de 6 blocs) mesure ainsi **14 blocs de long**.

Les distances se comptent sur l'axe des voies, au centre des blocs. Une courbe plus large que la norme est toujours permise, et même préférable sur une ligne rapide.

## Signalisation

Les signaux découpent le réseau en **sections** (ou cantons). Un train n'entre dans une section que si aucun autre train ne l'occupe. Deux types de signaux sont utilisés :

- le **signal simple** laisse passer le train si la section qui le suit immédiatement est libre ;
- le **signal chaîné** ne laisse passer le train que s'il peut aussi **ressortir** de la section suivante, c'est-à-dire si la section d'après est libre elle aussi. Un train ne s'arrête ainsi jamais au milieu d'un aiguillage, où il bloquerait les autres voies.

Les signaux chaînés s'enchaînent : un signal chaîné n'est vert que si le signal suivant sur le trajet l'est aussi. Une suite de signaux chaînés oblige donc le train à attendre que **tout le trajet** soit libre, jusqu'au premier signal simple. C'est voulu sur un aiguillage, mais à éviter là où un train peut attendre sans gêner, comme un quai.

Dans Create, un même bloc de signal fait les deux : il est simple par défaut et devient chaîné quand on change son mode à la clé.

Les règles à respecter :

1. **Avant une zone d'aiguillages ou de croisements** : un signal **chaîné**.
2. **À la sortie** de cette zone : un signal **simple**.
3. **Sur une voie de passage à double sens** : à chaque extrémité, un signal **chaîné dans chaque sens**. Un train n'y entre que s'il peut la traverser en entier.
4. **Sur une voie à quai** : un signal **simple** pour y entrer (le train peut attendre à quai) et un signal **chaîné** pour en sortir vers un aiguillage.
5. Une section à double sens ne contient **aucun signal intermédiaire** : elle forme une seule section, que deux trains ne peuvent pas occuper en même temps, et aucun train ne peut donc y arriver face à un autre.
6. Le long d'une voie normale, les signaux simples peuvent être espacés librement ; plus ils sont rapprochés, plus les trains peuvent se suivre de près.

## Intersection en T

![Intersection en T : une ligne principale à double voie et une ligne secondaire raccordée vers le sud, avec des signaux chaînés à chaque entrée et des signaux simples à chaque sortie](/images/docs/ferroviaire/intersection_t.svg)

Une ligne secondaire se raccorde à la ligne principale par une intersection en T. Les quatre mouvements sont possibles : depuis chaque sens de la ligne principale vers la ligne secondaire, et inversement. Chacun est un virage à 90° de **rayon 8**.

L'ensemble occupe environ **23 blocs de long** sur la ligne principale (de la première à la dernière courbe) et **15 blocs** sur la ligne secondaire. Les virages venant de la voie la plus éloignée croisent l'autre voie de la ligne principale à angle droit.

- Les **trois voies qui entrent** dans l'intersection (les deux voies de la ligne principale et la voie montante de la ligne secondaire) sont protégées par un **signal chaîné**, placé avant le premier aiguillage.
- Les **trois voies qui en sortent** reçoivent un **signal simple**, juste après le dernier aiguillage.

Toute la zone d'aiguillages ne forme ainsi qu'une seule section : un train n'y entre que s'il est sûr de pouvoir en sortir.

## Gare : quai le long de la ligne

![Gare le long de la ligne : deux doubles communications encadrent une section où les deux voies sont à double sens, avec un quai sur la voie de droite et la voie de gauche comme voie de passage](/images/docs/ferroviaire/gare_quai_lateral.svg)

C'est le modèle de gare de passage, construit directement sur la ligne sans l'élargir.

- La gare est encadrée par deux **doubles communications** : deux courbes en S croisées qui permettent de passer d'une voie à l'autre dans les deux sens. Chacune mesure **14 blocs de long** (voir [Courbes](#courbes)).
- Entre ces deux doubles communications, les voies forment une **section banalisée** : elles peuvent être parcourues dans les deux sens. Un train peut ainsi rejoindre un quai quelle que soit sa voie d'origine, ou repartir dans l'autre sens.
- La **longueur du quai**, et donc celle de la section banalisée, reste à définir.

### Disposition des quais

Le schéma montre un seul quai, le long de la voie de droite. Ce n'est qu'un exemple : on peut placer le quai à gauche, mettre un quai de chaque côté, construire un quai central entre deux voies, ajouter des voies à quai…

Une seule règle est obligatoire : la gare doit toujours garder une **voie de passage**, sans quai, où un train qui ne s'arrête pas peut traverser la gare. Quand il y a des quais des deux côtés, c'est la voie du milieu. Elle est équipée, **à chacune de ses extrémités, d'une paire de signaux chaînés** (un par sens). Les voies à quai, elles, suivent la règle des quais : signal simple pour y entrer, chaîné pour en sortir (voir ci-dessous).

### Signalisation

- À l'**entrée** de chaque double communication : un **signal chaîné**.
- À la **sortie** de la gare, sur la ligne : un **signal simple**.
- À chaque extrémité de la section banalisée, chaque voie a une paire de signaux, un par sens. Leur type dépend de la voie :

| Voie | Signal pour y entrer | Signal pour en sortir vers la double communication |
| --- | --- | --- |
| Voie à quai | **simple** | **chaîné** |
| Voie de passage | **chaîné** | **chaîné** |

- Aucun signal entre les deux extrémités : chaque voie de la section banalisée forme une seule section. Deux trains ne peuvent pas l'occuper en même temps, donc aucun ne peut s'y engager face à un autre.

Sur une voie à quai, le signal chaîné d'entrée de la double communication est suivi d'un signal simple : il n'exige donc que la **voie à quai libre**, pas la sortie de la gare. Le train entre et peut être obligé d'**attendre à quai** que la voie devant lui se libère. Ce n'est pas un problème, puisqu'il attend en gare et non au milieu d'un aiguillage. Son signal de sortie, chaîné, ne le laisse repartir que s'il peut traverser la double communication suivante sans s'y arrêter.

Sur la voie de passage, au contraire, tous les signaux sont chaînés : un train qui ne s'arrête pas n'y entre que s'il peut traverser toute la gare, et il n'immobilise jamais la seule voie de passage.

## Mode terminus : la raquette

![Raquette de retournement : en fin de ligne, la voie montante fait une boucle et revient sur la voie descendante](/images/docs/ferroviaire/terminus_raquette.svg)

En bout de ligne, les deux voies sont reliées par une **boucle de retournement**, appelée raquette. Le train qui arrive sur sa voie fait le tour de la boucle et repart sur l'autre voie, dans l'autre sens, sans manœuvre ni changement de conducteur.

La boucle est faite de **deux virages à 90° de rayon 8**. Ils demandent 16 blocs entre les deux voies, alors qu'elles n'en ont que 6. Chaque voie s'écarte donc d'abord de 5 blocs par une **courbe en S de 12 blocs**. La raquette occupe en tout **17 blocs de large** et une vingtaine de blocs de long.

La boucle n'est parcourue que dans un seul sens : elle n'a pas besoin de signal particulier. Une gare terminus peut être placée sur la boucle elle-même ou juste avant.

---

Des constructions prêtes à poser sont partagées dans la [galerie de schematics](/schematiques). Celles qu'un admin trains a vérifiées portent le badge **« Conforme aux normes »** ([voir uniquement celles-ci](/schematiques?conforme=1)).
