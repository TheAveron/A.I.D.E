# Normes ferroviaires

Le réseau d'Age of Steam est construit par de nombreux joueurs. Pour que deux lignes construites séparément puissent se raccorder, et que les trains y circulent sans se percuter ni se bloquer, toutes les voies du réseau suivent les normes ci-dessous.

Ces normes s'appliquent à toute nouvelle construction raccordée au réseau. Une voie privée, isolée du reste (dans une usine par exemple), peut s'en écarter.

**Sommaire**

- [Légende des schémas](#légende-des-schémas)
- [Principes généraux](#principes-généraux)
- [Gabarit d'une ligne](#gabarit-dune-ligne)
- [Tunnels](#tunnels)
- [Signalisation](#signalisation)
- [Intersection en T](#intersection-en-t)
- [Gare : quai le long de la ligne](#gare--quai-le-long-de-la-ligne)
- [Mode terminus : la raquette](#mode-terminus--la-raquette)

## Légende des schémas

Tous les schémas utilisent les mêmes symboles :

| Symbole | Signification |
| --- | --- |
| Chevron **orange** | Sens de circulation de la voie |
| Deux chevrons **orange** opposés | Voie à double sens (section banalisée) |
| Chevron **rouge** simple | Signal simple, placé dans le sens qu'il protège |
| Double chevron **rouge** | Signal chaîné, placé dans le sens qu'il protège |
| Cadre rouge en pointillés | Zone d'aiguillages ou de croisements |

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

## Signalisation

Les signaux découpent le réseau en **sections** (ou cantons). Un train n'entre dans une section que si aucun autre train ne l'occupe. Deux types de signaux sont utilisés :

- le **signal simple** laisse passer le train si la section qui le suit immédiatement est libre ;
- le **signal chaîné** ne laisse passer le train que s'il peut aussi **ressortir** de la section suivante, c'est-à-dire si la section d'après est libre elle aussi. Un train ne s'arrête ainsi jamais au milieu d'un aiguillage, où il bloquerait les autres voies.

Dans Create, un même bloc de signal fait les deux : il est simple par défaut et devient chaîné quand on change son mode à la clé.

Les règles à respecter :

1. **Avant une zone d'aiguillages ou de croisements** : un signal **chaîné**.
2. **À la sortie** de cette zone : un signal **simple**.
3. **À chaque extrémité d'une section à double sens** : un signal **chaîné dans chaque sens**, pour qu'un train n'y entre jamais face à un autre.
4. Le long d'une voie normale, les signaux simples peuvent être espacés librement ; plus ils sont rapprochés, plus les trains peuvent se suivre de près.

## Intersection en T

![Intersection en T : une ligne principale à double voie et une ligne secondaire raccordée vers le sud, avec des signaux chaînés à chaque entrée et des signaux simples à chaque sortie](/images/docs/ferroviaire/intersection_t.svg)

Une ligne secondaire se raccorde à la ligne principale par une intersection en T. Les quatre mouvements sont possibles : depuis chaque sens de la ligne principale vers la ligne secondaire, et inversement.

- Les **trois voies qui entrent** dans l'intersection (les deux voies de la ligne principale et la voie montante de la ligne secondaire) sont protégées par un **signal chaîné**, placé avant le premier aiguillage.
- Les **trois voies qui en sortent** reçoivent un **signal simple**, juste après le dernier aiguillage.

Toute la zone d'aiguillages ne forme ainsi qu'une seule section : un train n'y entre que s'il est sûr de pouvoir en sortir.

## Gare : quai le long de la ligne

![Gare le long de la ligne : deux doubles communications encadrent une section où les deux voies sont à double sens, avec le quai sur la voie de droite](/images/docs/ferroviaire/gare_quai_lateral.svg)

C'est le modèle de gare de passage, construit directement sur la ligne sans l'élargir.

- Le **quai** est placé le long de la voie de droite.
- La gare est encadrée par deux **doubles communications** : deux aiguillages croisés qui permettent de passer d'une voie à l'autre dans les deux sens.
- Entre ces deux doubles communications, les deux voies forment une **section banalisée** : elles peuvent être parcourues dans les deux sens. Un train peut ainsi rejoindre le quai quelle que soit sa voie d'origine, ou repartir dans l'autre sens.

Signalisation :

- à l'**entrée** de chaque double communication : un **signal chaîné** ;
- à la **sortie** de la gare, sur la ligne : un **signal simple** ;
- à **chaque extrémité de la section banalisée**, sur chaque voie : un **signal chaîné dans chaque sens**. Ce sont eux qui empêchent deux trains de s'engager face à face sur la même voie.

## Mode terminus : la raquette

![Raquette de retournement : en fin de ligne, la voie montante fait une boucle et revient sur la voie descendante](/images/docs/ferroviaire/terminus_raquette.svg)

En bout de ligne, les deux voies sont reliées par une **boucle de retournement**, appelée raquette. Le train qui arrive sur sa voie fait le tour de la boucle et repart sur l'autre voie, dans l'autre sens, sans manœuvre ni changement de conducteur.

La boucle n'est parcourue que dans un seul sens : elle n'a pas besoin de signal particulier. Une gare terminus peut être placée sur la boucle elle-même ou juste avant.

---

_À venir : une bibliothèque de schematics prêtes à poser, conformes à ces normes._
