from django.contrib import admin
from .models import (
    Enseignant, Module, AffectationTheorique, HistoriqueAffectation,
    PlanEtude, SeanceEmploiDuTemps, Presence, Voeu, EmailEnvoye
)

admin.site.register(Enseignant)
admin.site.register(Module)
admin.site.register(AffectationTheorique)
admin.site.register(HistoriqueAffectation)
admin.site.register(PlanEtude)
admin.site.register(SeanceEmploiDuTemps)
admin.site.register(Presence)
admin.site.register(Voeu)
admin.site.register(EmailEnvoye)