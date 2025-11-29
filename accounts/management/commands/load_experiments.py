from django.core.management.base import BaseCommand
from accounts.models import Experiment

class Command(BaseCommand):
    help = 'Load initial experiment data'

    def handle(self, *args, **options):
        experiments = [
            {'exp_key': 'exp1', 'name': 'Exp#1 OAI Core', 'description': 'Test and validate OAI core network', 'url': 'http://10.7.43.10:4040'},
            {'exp_key': 'exp2', 'name': 'Exp#2 OAI+gNB', 'description': 'Run gNB tests with OAI Core', 'url': 'http://10.7.43.11:4040'},
            {'exp_key': 'exp3', 'name': 'Exp#3 OAI+gNB+UE', 'description': 'Simulate UE connections', 'url': 'http://10.7.43.12:4040'},
            {'exp_key': 'exp4', 'name': 'Exp#4 Open5GS', 'description': 'Manage Open5GS core network', 'url': 'http://10.7.43.13:4040'},
            {'exp_key': 'exp5', 'name': 'Exp#5 Free5GC', 'description': 'Access Free5GC environment', 'url': 'http://10.7.43.14:4040'},
        ]
        
        for exp_data in experiments:
            exp, created = Experiment.objects.get_or_create(
                exp_key=exp_data['exp_key'],
                defaults=exp_data
            )
            if created:
                self.stdout.write(f"Created {exp.name}")
            else:
                self.stdout.write(f"Already exists: {exp.name}")