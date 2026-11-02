#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import math
from dronekit import connect, VehicleMode, LocationGlobalRelative
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# =====================================================
# 1. CONFIGURATION & ZONES SENSIBLES
# =====================================================
RAYON_SECURITE = 1500
ZONES_INTERDITES = [
    {"nom": "Aéroport Ndjili", "lat": -4.3856, "lon": 15.4446},
    {"nom": "Aérodrome Ndolo", "lat": -4.3250, "lon": 15.3222},
    {"nom": "Présidence", "lat": -4.3015, "lon": 15.3050}
]

# Points de passage forcés (Transit)
TRAJET_TRANSIT = [
    {"lat": -4.3100, "lon": 15.3100},
    {"lat": -4.3200, "lon": 15.3150}
]


def est_zone_securisee(lat, lon):
    for zone in ZONES_INTERDITES:
        dist = geodesic((lat, lon), (zone["lat"], zone["lon"])).meters
        if dist < RAYON_SECURITE:
            print(f"⚠️Attention,Ici le groupe 4,Vous franchissez la zone interdite : {zone['nom']} à {int(dist)}m")
            return False
    return True


# =====================================================
# 2. PILOTAGE ET ATTENTE
# =====================================================
connection_string = "tcp:127.0.0.1:5763"
print("Connexion au drone...")
vehicle = connect(connection_string, wait_ready=True)

# User-agent unique pour éviter les blocages Nominatim en 2025
geolocator = Nominatim(user_agent="mission_agri_kin_2025_v9")


def aller_a(lat, lon, alt):
    """ Envoie le drone et attend l'arrivée horizontale uniquement """
    target = LocationGlobalRelative(lat, lon, alt)
    if est_zone_securisee(lat, lon):
        vehicle.simple_goto(target)
        while True:
            curr = vehicle.location.global_relative_frame
            dist = geodesic((curr.lat, curr.lon), (lat, lon)).meters
            if dist < 2.0:  # Arrivé à 2 mètres près
                break
            time.sleep(1)
        return True
    return False


def changer_altitude(cible_alt):
    """ Change l'altitude verticalement et attend d'y être """
    print(f"↕️ Changement d'altitude vers {cible_alt}m...")
    target = LocationGlobalRelative(vehicle.location.global_relative_frame.lat,
                                    vehicle.location.global_relative_frame.lon,
                                    cible_alt)
    vehicle.simple_goto(target)
    while True:
        alt_actuelle = vehicle.location.global_relative_frame.alt
        if abs(alt_actuelle - cible_alt) < 0.5:
            break
        print(f" Altitude : {alt_actuelle:.1f}m")
        time.sleep(1)


# =====================================================
# 3. MISSION DE SEMIS
# =====================================================
def zigzag_semis(lat, lon, alt):
    print("🌱 Lancement du semis (90x30m)...")
    longueur, largeur, pas = 90, 30, 8
    nb_lignes = int(largeur / pas) + 1

    for i in range(nb_lignes):
        offset_lon = (i * pas) / (111320.0 * math.cos(math.radians(lat)))
        curr_lon = lon + offset_lon

        lat_n = lat + (45 / 111320.0)
        lat_s = lat - (45 / 111320.0)

        points = [(lat_s, curr_lon), (lat_n, curr_lon)]
        if i % 2 != 0: points.reverse()

        for p_lat, p_lon in points:
            aller_a(p_lat, p_lon, alt)
        print(f" Ligne {i + 1}/{nb_lignes} terminée.")


# =====================================================
# 4. EXÉCUTION
# =====================================================
try:
    alt_transit = float(input("Altitude de transit (m) : "))
    adresse = input("Adresse du champ : ")

    location = geolocator.geocode(adresse)
    if not location:
        print("❌ GPS : Adresse non reconnue par les serveurs.")
    elif not est_zone_securisee(location.latitude, location.longitude):
        print("❌ GPS : Le champ est en zone interdite !")
    else:
        # A. Décollage
        print("Armement...")
        while not vehicle.is_armable: time.sleep(1)
        vehicle.mode = VehicleMode("GUIDED")
        vehicle.armed = True
        vehicle.simple_takeoff(alt_transit)
        changer_altitude(alt_transit)

        # B. Transit personnalisé
        print("Début du transit personnalisé...")
        for pt in TRAJET_TRANSIT:
            aller_a(pt['lat'], pt['lon'], alt_transit)

        # C. Aller au champ et descendre
        print("Arrivée au champ...")
        aller_a(location.latitude, location.longitude, alt_transit)
        changer_altitude(20.0)  # Altitude de semis

        # D. Semis
        zigzag_semis(location.latitude, location.longitude, 20.0)

        # E. Remontée et Retour (CORRECTION RTL)
        print("Mission terminée !")
        changer_altitude(alt_transit)  # Remonte à l'altitude initiale (ex: 50m)

        print("RTL activé...")
        vehicle.mode = VehicleMode("RTL")

except Exception as e:
    print(f"Erreur système : {e}")
finally:
    vehicle.close()
