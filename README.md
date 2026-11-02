# DroneSemis

Programme Python de mission autonome pour un drone agricole de semis, destiné aux champs autour de Kinshasa (RDC). Projet intégrateur réalisé en équipe (groupe 4) à l'Université Loyola du Congo.

## Ce que fait le programme
- Demande l'altitude de transit et l'adresse du champ, puis trouve ses coordonnées GPS (géolocalisation)
- Vérifie que le champ et chaque point de passage sont hors des zones interdites (aéroports et sites sensibles, rayon de sécurité de 1,5 km)
- Arme le drone, décolle et suit un trajet de transit prédéfini
- Descend à 20 m et couvre un champ de 90 x 30 m en zigzag pour le semis
- Remonte à l'altitude de transit et lance le retour automatique (RTL)

## Technologies
Python, DroneKit, Geopy (Nominatim)

## Fichier principal
`Code_de_base.py`

## Remarque
Le programme se connecte au drone par une connexion locale (127.0.0.1), prévue pour un simulateur.
