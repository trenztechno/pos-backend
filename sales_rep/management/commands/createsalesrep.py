from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from auth_app.models import SalesRep

class Command(BaseCommand):
    help = 'Create a sales rep user'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username for the sales rep')
        parser.add_argument('--email', type=str, help='Email for the sales rep')
        parser.add_argument('--password', type=str, help='Password for the sales rep')
        parser.add_argument('--name', type=str, help='Full name of the sales rep')
        parser.add_argument('--phone', type=str, help='Phone number of the sales rep')

    def handle(self, *args, **options):
        username = options['username']
        email = options.get('email', f'{username}@pos.local')
        password = options.get('password', 'salesrep123')
        name = options.get('name', '')
        phone = options.get('phone', '')
        
        # Create user
        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists. Updating...'))
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                is_active=True
            )
            self.stdout.write(self.style.SUCCESS(f'User {username} created'))
        
        # Create or update sales rep profile
        sales_rep, created = SalesRep.objects.get_or_create(user=user)
        sales_rep.name = name
        sales_rep.phone = phone
        sales_rep.is_active = True
        sales_rep.save()
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Sales rep profile created for {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Sales rep profile updated for {username}'))
        
        self.stdout.write(self.style.SUCCESS(f'\nSales Rep created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'Login URL: http://localhost:8000/sales-rep/'))

