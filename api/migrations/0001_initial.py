# Generated by Django 5.1.2 on 2024-12-25 15:09

import api.models
import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'department',
            },
        ),
        migrations.CreateModel(
            name='Gender',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=10)),
            ],
            options={
                'db_table': 'gender',
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255)),
            ],
            options={
                'db_table': 'role',
            },
        ),
        migrations.CreateModel(
            name='RoomState',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'verbose_name': 'Room State',
                'verbose_name_plural': 'Room States',
                'db_table': 'roomstate',
            },
        ),
        migrations.CreateModel(
            name='RoomStatus',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'roomstatus',
            },
        ),
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=255, unique=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.CreateModel(
            name='PasswordReset',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=255)),
                ('token', models.CharField(db_index=True, max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
                ('reset_channel', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS')], max_length=30)),
                ('expiry_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Password Reset',
                'verbose_name_plural': 'Password Resets',
                'db_table': 'passwordreset',
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=255)),
                ('birthdate', models.DateField(null=True)),
                ('photo', models.ImageField(null=True, upload_to=api.models.profile_photo_upload_path)),
                ('phone_number', models.CharField(blank=True, max_length=30, null=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('residential_address', models.CharField(blank=True, max_length=255, null=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profiles_created', to='api.profile')),
                ('department', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='profiles', to='api.department')),
                ('gender', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.gender')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'profile',
            },
        ),
        migrations.CreateModel(
            name='HotelView',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'verbose_name': 'Hotel View',
                'verbose_name_plural': 'Hotel Views',
                'db_table': 'hotelview',
            },
        ),
        migrations.CreateModel(
            name='HotelFloor',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'db_table': 'hotelfloor',
            },
        ),
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'verbose_name': 'Amenity',
                'verbose_name_plural': 'Amenities',
                'db_table': 'amenities',
            },
        ),
        migrations.CreateModel(
            name='ProfileRole',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='roles', to='api.profile')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='profiles', to='api.role')),
            ],
            options={
                'verbose_name': 'Profile Role',
                'verbose_name_plural': 'Profile Roles',
                'db_table': 'profilerole',
            },
        ),
        migrations.AddField(
            model_name='profile',
            name='profile_roles',
            field=models.ManyToManyField(through='api.ProfileRole', to='api.role'),
        ),
        migrations.CreateModel(
            name='RoomCategory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'verbose_name': 'Room Category',
                'verbose_name_plural': 'Room Categories',
                'db_table': 'roomcategory',
            },
        ),
        migrations.CreateModel(
            name='RoomStateTrans',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('final_trans_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='final_trans', to='api.roomstate')),
                ('initial_trans_state', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='initial_trans', to='api.roomstate')),
            ],
            options={
                'verbose_name': 'Room State Transfer',
                'verbose_name_plural': 'Room State Transfers',
                'db_table': 'roomstatetrans',
            },
        ),
        migrations.CreateModel(
            name='RoomType',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('area_in_meters', models.DecimalField(decimal_places=1, default=0.0, max_digits=4)),
                ('area_in_feet', models.DecimalField(decimal_places=1, default=0.0, max_digits=4)),
                ('max_guests', models.IntegerField(default=1)),
                ('bed', models.CharField(max_length=255)),
                ('price_per_night', models.DecimalField(decimal_places=2, default=0.0, max_digits=6)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('amenities', models.ManyToManyField(to='api.amenity')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('room_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.roomcategory')),
                ('view', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.hotelview')),
            ],
            options={
                'verbose_name': 'Room Type',
                'verbose_name_plural': 'Room Types',
                'db_table': 'roomtype',
            },
        ),
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('room_number', models.CharField(db_index=True, max_length=255)),
                ('price_per_night', models.DecimalField(decimal_places=2, default=0.0, max_digits=6)),
                ('is_occupied', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('floor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.hotelfloor')),
                ('room_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.roomtype')),
            ],
            options={
                'db_table': 'room',
            },
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('check_in', models.DateField(default=django.utils.timezone.now)),
                ('check_out', models.DateField(default=django.utils.timezone.now)),
                ('room', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.room')),
                ('room_category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.roomcategory')),
                ('room_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.roomtype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Shift',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255, unique=True)),
                ('start_time', models.TimeField(default=django.utils.timezone.now)),
                ('end_time', models.TimeField(default=django.utils.timezone.now)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RoomKeepingAssign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('assignment_date', models.DateField(default=django.utils.timezone.now)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('assigned_to', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='room_keeping_duties', to='api.profile')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_roomkeeping_assignments', to='api.profile')),
                ('last_modified_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='modified_roomkeeping_assignments', to='api.profile')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenance_assignments', to='api.room')),
                ('shift', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.shift')),
            ],
            options={
                'verbose_name': 'Room Keeping Assignment',
                'verbose_name_plural': 'Room Keeping Assignments',
                'db_table': 'roomkeepingassign',
            },
        ),
        migrations.CreateModel(
            name='ProfileShiftAssign',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('date', models.DateField(default=django.utils.timezone.now)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shifts', to='api.profile')),
                ('shift', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.shift')),
            ],
            options={
                'verbose_name': 'Shift Assignment',
                'verbose_name_plural': 'Shift Assignments',
                'db_table': 'profileshiftassign',
            },
        ),
        migrations.CreateModel(
            name='ProcessRoomKeeping',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('date_processed', models.DateTimeField(default=django.utils.timezone.now)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.profile')),
                ('room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.room')),
                ('room_state_trans', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.roomstatetrans')),
                ('shift', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.shift')),
            ],
            options={
                'verbose_name': 'Room Keeping',
                'verbose_name_plural': 'Room Keepings',
                'db_table': 'processroomkeeping',
            },
        ),
    ]
