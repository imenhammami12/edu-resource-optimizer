import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand

from core.models import (
    Enseignant, Module, PlanEtude, AffectationTheorique,
    SeanceEmploiDuTemps, Presence, Voeu, HistoriqueAffectation, EmailEnvoye
)

SEMESTRE_ACTUEL = "S2-2026"
SEMESTRES_PASSES = ["S1-2025", "S2-2025", "S1-2026"]
DEPARTEMENTS = ["Informatique", "Génie Civil", "Génie Électrique", "Mathématiques"]
GRADES = ["Assistant", "Maître assistant", "Maître de conférences", "Professeur"]
SALLES = ["A101", "A102", "B201", "B202", "C301", "Amphi 1", "Amphi 2"]

PRENOMS = [
    "Mohamed", "Ahmed", "Fatma", "Amira", "Youssef", "Sana", "Karim", "Nour",
    "Sofien", "Rania", "Wassim", "Ines", "Bilel", "Emna", "Anis", "Mariem",
    "Skander", "Hela", "Aymen", "Salma", "Rami", "Yasmine", "Firas", "Lina",
    "Nizar", "Dorra", "Hatem", "Sirine", "Chokri", "Meriem",
]
NOMS = [
    "Ben Ali", "Trabelsi", "Gharbi", "Bouazizi", "Sassi", "Jelassi", "Khemiri",
    "Mansouri", "Chaabane", "Bouzid", "Hamdi", "Cherni", "Karray", "Fenina",
    "Zaoui", "Belhaj", "Souissi", "Aouadi", "Nasri", "Rekik",
]
NOMS_MODULES = [
    "Algorithmique", "Bases de données", "Réseaux", "Systèmes d'exploitation",
    "Génie logiciel", "Intelligence artificielle", "Mathématiques discrètes",
    "Statistiques", "Programmation web", "Sécurité informatique",
    "Architecture des ordinateurs", "Compilation", "Cloud computing",
    "Structures de données", "Analyse numérique", "Probabilités",
    "Systèmes distribués", "Machine Learning", "Génie civil appliqué",
    "Électronique numérique",
]
COMMENTAIRES_PRESENCE = [
    "Certificat médical fourni", "Retard justifié par embouteillage",
    "Absence signalée à l'avance", "Rattrapage à planifier", "",
]
OBJETS_EMAIL = [
    "Collecte de vos voeux pour le semestre",
    "Rappel : formulaire de préférences à remplir",
    "Alerte : séance non rattrapée",
    "Relance : rattrapage à programmer",
]


def nom_complet_module(i):
    """Génère un nom de module unique même si on dépasse la liste de base."""
    base = NOMS_MODULES[i % len(NOMS_MODULES)]
    tour = i // len(NOMS_MODULES)
    return base if tour == 0 else f"{base} {tour + 1}"


class Command(BaseCommand):
    help = "Génère des données de test réalistes pour tous les modèles (sans dépendance externe)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Supprime toutes les données existantes avant de générer",
        )

    def handle(self, *args, **options):
        if options["flush"]:
            self.stdout.write("Suppression des données existantes...")
            EmailEnvoye.objects.all().delete()
            HistoriqueAffectation.objects.all().delete()
            Voeu.objects.all().delete()
            Presence.objects.all().delete()
            SeanceEmploiDuTemps.objects.all().delete()
            AffectationTheorique.objects.all().delete()
            PlanEtude.objects.all().delete()
            Module.objects.all().delete()
            Enseignant.objects.all().delete()

        enseignants = self.creer_enseignants(15)
        modules = self.creer_modules(20)
        self.creer_plans_etudes(modules)
        affectations = self.creer_affectations_theoriques(enseignants, modules)
        seances = self.creer_seances(affectations)
        self.creer_presences(seances)
        self.creer_voeux(enseignants, modules)
        self.creer_historique(enseignants, modules)
        self.creer_emails(enseignants)

        self.stdout.write(self.style.SUCCESS("Données générées avec succès !"))

    def creer_enseignants(self, n):
        self.stdout.write(f"Création de {n} enseignants...")
        enseignants = []
        prenoms_utilises = random.sample(PRENOMS, min(n, len(PRENOMS)))
        for i in range(n):
            prenom = prenoms_utilises[i] if i < len(prenoms_utilises) else random.choice(PRENOMS)
            nom = random.choice(NOMS)
            email = f"{prenom.lower()}.{nom.lower().replace(' ', '')}{i}@universite.tn"
            e = Enseignant.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                grade=random.choice(GRADES),
                statut=random.choice([Enseignant.Statut.PERMANENT, Enseignant.Statut.VACATAIRE]),
                departement=random.choice(DEPARTEMENTS),
                quota_heures_max=random.choice([96.0, 144.0, 192.0]),
            )
            enseignants.append(e)
        return enseignants

    def creer_modules(self, n):
        self.stdout.write(f"Création de {n} modules...")
        modules = []
        for i in range(n):
            m = Module.objects.create(
                nom=nom_complet_module(i),
                coefficient=random.choice([1.0, 1.5, 2.0, 2.5, 3.0]),
                type_enseignement=random.choice(
                    [Module.TypeEnseignement.CM, Module.TypeEnseignement.TD, Module.TypeEnseignement.TP]
                ),
                volume_horaire_theorique=random.choice([21.0, 28.0, 42.0]),
                semestre=SEMESTRE_ACTUEL,
                departement=random.choice(DEPARTEMENTS),
            )
            modules.append(m)
        return modules

    def creer_plans_etudes(self, modules):
        self.stdout.write("Création des plans d'études...")
        for m in modules:
            PlanEtude.objects.create(module=m, semestre=SEMESTRE_ACTUEL, est_valide=True)

    def creer_affectations_theoriques(self, enseignants, modules):
        self.stdout.write("Création des affectations théoriques...")
        affectations = []
        for m in modules:
            enseignant = random.choice(enseignants)
            try:
                a = AffectationTheorique.objects.create(
                    enseignant=enseignant, module=m, semestre=SEMESTRE_ACTUEL,
                )
                affectations.append(a)
            except Exception:
                pass
        return affectations

    def creer_seances(self, affectations):
        self.stdout.write("Création des séances d'emploi du temps...")
        seances = []
        for a in affectations:
            autres_enseignants = list(
                Enseignant.objects.exclude(id=a.enseignant.id)
            )
            for _ in range(random.randint(2, 4)):
                # 15% de chance de divergence volontaire -> matière à l'Axe 3 (audit)
                enseignant_seance = a.enseignant
                if autres_enseignants and random.random() < 0.15:
                    enseignant_seance = random.choice(autres_enseignants)

                heure_debut_h = random.choice([8, 10, 12, 14, 16])
                s = SeanceEmploiDuTemps.objects.create(
                    module=a.module,
                    enseignant=enseignant_seance,
                    date_seance=date(2026, 2, 1) + timedelta(days=random.randint(0, 90)),
                    heure_debut=f"{heure_debut_h:02d}:30",
                    heure_fin=f"{heure_debut_h + 1:02d}:30",
                    salle=random.choice(SALLES),
                    semestre=SEMESTRE_ACTUEL,
                )
                seances.append(s)
        return seances

    def creer_presences(self, seances):
        self.stdout.write("Création des présences...")
        statuts_pond = (
            [Presence.Statut.PRESENT] * 15
            + [Presence.Statut.RETARD] * 3
            + [Presence.Statut.ABSENT_JUSTIFIE] * 2
            + [Presence.Statut.MALADIE] * 2
            + [Presence.Statut.ABSENT_INJUSTIFIE] * 1
        )
        for s in seances:
            Presence.objects.create(
                enseignant=s.enseignant,
                seance=s,
                date_evenement=s.date_seance,
                statut=random.choice(statuts_pond),
                commentaire=random.choice(COMMENTAIRES_PRESENCE),
            )

    def creer_voeux(self, enseignants, modules):
        self.stdout.write("Création des vœux...")
        for e in enseignants:
            for m in random.sample(modules, k=random.randint(2, 5)):
                Voeu.objects.create(
                    enseignant=e,
                    module=m,
                    semestre=SEMESTRE_ACTUEL,
                    score_preference=round(random.uniform(0.1, 1.0), 2),
                )

    def creer_historique(self, enseignants, modules):
        self.stdout.write("Création de l'historique des affectations (pour le ML)...")
        for semestre in SEMESTRES_PASSES:
            for _ in range(30):
                enseignant = random.choice(enseignants)
                module = random.choice(modules)
                heures_theo = random.choice([21.0, 28.0, 42.0])
                a_ete_affecte = random.random() > 0.1
                heures_real = (
                    round(heures_theo * random.uniform(0.7, 1.0), 1)
                    if a_ete_affecte else 0.0
                )
                HistoriqueAffectation.objects.create(
                    enseignant=enseignant,
                    module=module,
                    semestre=semestre,
                    a_ete_affecte=a_ete_affecte,
                    heures_realisees=heures_real,
                    heures_theoriques=heures_theo,
                )

    def creer_emails(self, enseignants):
        self.stdout.write("Création des emails envoyés...")
        types_email = ["voeux", "alerte_rattrapage", "relance"]
        for e in enseignants:
            for _ in range(random.randint(1, 3)):
                EmailEnvoye.objects.create(
                    destinataire=e.email,
                    type_email=random.choice(types_email),
                    objet=random.choice(OBJETS_EMAIL),
                    statut_envoi=random.choice(["envoye", "envoye", "envoye", "echec"]),
                )