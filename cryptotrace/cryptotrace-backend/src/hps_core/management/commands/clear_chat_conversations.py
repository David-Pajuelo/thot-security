"""
Borra todas las conversaciones de chat y sus mensajes.
Útil para empezar de cero tras cambiar la lógica de guardado (solo mensajes usuario/bot, sin bienvenida).
"""
from django.core.management.base import BaseCommand
from hps_core.models import ChatConversation, ChatMessage


class Command(BaseCommand):
    help = "Borra todas las conversaciones de chat y sus mensajes (empezar de cero)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="No pedir confirmación",
        )

    def handle(self, *args, **options):
        msg_count = ChatMessage.objects.count()
        conv_count = ChatConversation.objects.count()

        if conv_count == 0:
            self.stdout.write(self.style.WARNING("No hay conversaciones de chat que borrar."))
            return

        if not options["no_input"]:
            confirm = input(
                f"Se borrarán {conv_count} conversaciones y {msg_count} mensajes. ¿Continuar? [y/N]: "
            )
            if confirm.lower() != "y":
                self.stdout.write("Operación cancelada.")
                return

        # Borrar conversaciones (los mensajes se borran en cascada)
        ChatConversation.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(f"✅ Borradas {conv_count} conversaciones y {msg_count} mensajes.")
        )
