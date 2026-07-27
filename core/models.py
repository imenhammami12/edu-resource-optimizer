"""
Modèle de données unifié du projet — version Django.

Ce fichier est LA fondation du projet : Axe 1 (BI), Axe 2 (suivi RH),
Axe 3 (audit) et Axe 4 (ML) lisent/écrivent tous dans ces tables.
=> Toute modification doit être validée par le binôme avant merge.
"""

from django.db import models


class Enseignant(models.Model):
    class Statut(models.TextChoices):
        PERMANENT = "permanent", "Permanent"
        VACATAIRE = "vacataire", "Vacataire"

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    grade = models.CharField(max_length=50, blank=True)  # Assistant, Maître assistant, Professeur...
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.PERMANENT)
    departement = models.CharField(max_length=100, blank=True)
    quota_heures_max = models.FloatField(default=192.0)  # quota réglementaire annuel

    def __str__(self):
        return f"{self.prenom} {self.nom}"


class Module(models.Model):
    class TypeEnseignement(models.TextChoices):
        CM = "CM", "Cours Magistral"
        TD = "TD", "Travaux Dirigés"
        TP = "TP", "Travaux Pratiques"

    nom = models.CharField(max_length=150)
    coefficient = models.FloatField(default=1.0)
    type_enseignement = models.CharField(max_length=2, choices=TypeEnseignement.choices)
    volume_horaire_theorique = models.FloatField()
    semestre = models.CharField(max_length=20)  # ex: "S1-2026"
    departement = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.semestre})"


class PlanEtude(models.Model):
    """Ce qui est officiellement prévu au programme pour un semestre donné."""
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="plans_etudes")
    semestre = models.CharField(max_length=20)
    est_valide = models.BooleanField(default=True)


class AffectationTheorique(models.Model):
    """Qui est censé enseigner quoi, décidé par le responsable de département."""
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name="affectations")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="affectations")
    semestre = models.CharField(max_length=20)

    class Meta:
        unique_together = ("enseignant", "module", "semestre")


class SeanceEmploiDuTemps(models.Model):
    """Ce qui est réellement planifié sur la grille horaire (peut diverger de l'affectation théorique)."""
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    date_seance = models.DateField()
    heure_debut = models.CharField(max_length=5)  # "08:30"
    heure_fin = models.CharField(max_length=5)
    salle = models.CharField(max_length=50, blank=True)
    semestre = models.CharField(max_length=20)


class Presence(models.Model):
    class Statut(models.TextChoices):
        PRESENT = "present", "Présent"
        ABSENT_JUSTIFIE = "absent_justifie", "Absent justifié"
        ABSENT_INJUSTIFIE = "absent_injustifie", "Absent injustifié"
        MALADIE = "maladie", "Maladie"
        RETARD = "retard", "Retard"

    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name="presences")
    seance = models.ForeignKey(SeanceEmploiDuTemps, on_delete=models.SET_NULL, null=True, blank=True)
    date_evenement = models.DateField()
    statut = models.CharField(max_length=30, choices=Statut.choices)
    commentaire = models.CharField(max_length=255, blank=True)


class Voeu(models.Model):
    """Préférences exprimées par un enseignant pour un module donné."""
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name="voeux")
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=20)
    score_preference = models.FloatField(default=0.5)  # 0 = pas intéressé, 1 = très intéressé


class HistoriqueAffectation(models.Model):
    """
    Table d'entraînement du modèle ML : pour chaque semestre passé,
    a-t-on affecté cet enseignant à ce module, et combien d'heures
    ont réellement été faites vs prévues.
    """
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    semestre = models.CharField(max_length=20)
    a_ete_affecte = models.BooleanField(default=True)  # label pour le ML
    heures_realisees = models.FloatField(default=0.0)
    heures_theoriques = models.FloatField(default=0.0)


class EmailEnvoye(models.Model):
    destinataire = models.EmailField()
    type_email = models.CharField(max_length=50)  # "voeux", "alerte_rattrapage", "relance"
    date_envoi = models.DateTimeField(auto_now_add=True)
    objet = models.CharField(max_length=200)
    statut_envoi = models.CharField(max_length=20, default="envoye")  # envoye / echec