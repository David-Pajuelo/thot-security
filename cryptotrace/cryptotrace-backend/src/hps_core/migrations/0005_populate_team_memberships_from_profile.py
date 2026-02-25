# Migración de datos: crear HpsTeamMembership desde HpsUserProfile.team
# Permite que la fuente de verdad para "usuarios en equipos" sea HpsTeamMembership (N:N).

from django.db import migrations


def populate_team_memberships(apps, schema_editor):
    HpsUserProfile = apps.get_model("hps_core", "HpsUserProfile")
    HpsTeamMembership = apps.get_model("hps_core", "HpsTeamMembership")

    created = 0
    for profile in HpsUserProfile.objects.select_related("team", "user").filter(team__isnull=False):
        team = profile.team
        user = profile.user
        if not team or not user:
            continue
        if HpsTeamMembership.objects.filter(team=team, user=user).exists():
            continue
        is_lead = team.team_lead_id == user.id if team.team_lead_id else False
        HpsTeamMembership.objects.create(
            team=team,
            user=user,
            is_active=True,
            is_lead=is_lead,
        )
        created += 1

    if created:
        print(f"  [hps_core] Creadas {created} membresías de equipo desde HpsUserProfile.team")


def noop_reverse(apps, schema_editor):
    # No borramos memberships al hacer rollback; los datos pueden seguir usándose
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("hps_core", "0004_add_waiting_dps_status"),
    ]

    operations = [
        migrations.RunPython(populate_team_memberships, noop_reverse),
    ]
