from .. import models as api_models
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group
import datetime
from rest_framework_simplejwt.tokens import RefreshToken


class AuthenticationTest(TestCase):
    @classmethod
    def setUpTestData(self):
        self.male = api_models.Gender.objects.create(name="Male")
        self.female = api_models.Gender.objects.create(name="Female")
        self.housekeeping_dpt = api_models.Department.objects.create(
            name="House Keeping"
        )
        self.general_dpt = api_models.Department.objects.create(name="General")
        self.supervisor = api_models.Role.objects.create(name="Supervisor")
        self.staff = api_models.Role.objects.create(name="Staff")
        self.admin = api_models.Role.objects.create(name="Admin")

        self.new_user_data = {
            "user": {
                "username": "new_user",
                "first_name": "hod housekeeping",
                "last_name": "kempinski",
                "password": "housekeeping_hod",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            "department": self.general_dpt.name,
            "roles": [
                {
                    # "role": {"name": self.staff.name},
                    "role": self.staff.name,
                    "is_active": True,
                }
                # self.staff.name
            ],
            "gender": self.female.name,
        }

        self.system_user_data = {
            "user": {
                "username": "system_user",
                "first_name": "System",
                "last_name": "Kempinski",
                "password": "secret",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            "department": {"id": self.general_dpt.id, "name": self.general_dpt.name},
            "roles": [
                {
                    "id": "",
                    "role": {"id": self.admin.id, "name": self.admin.name},
                    "is_active": True,
                }
            ],
            "gender": {"id": self.male.id, "name": self.male.name},
        }

        # print(self.system_user_data)
        api_models.CustomUser.objects.create_user(**self.system_user_data.pop("user"))

        # create shifts
        shift_names = ["Morning", "Afternoon", "Evening"]
        shifts = [api_models.Shift(name=name) for name in shift_names]
        api_models.Shift.objects.bulk_create(shifts)

        group_names = ["Staff", "General"]
        groups = [Group(name=name) for name in group_names]
        Group.objects.bulk_create(groups)

    def setUp(self):
        # Create a user
        self.user = api_models.CustomUser.objects.get(username="system_user")
        self.system_user_profile = api_models.Profile.objects.create(
            user=self.user, full_name=f"{self.user.first_name} {self.user.last_name}"
        )
        self.housekeeping_dpt = api_models.Department.objects.get(
            name__iexact="housekeeping"
        )
        # print(self.housekeeping_dpt.id)

        self.housekeeping_hod_user_data = {
            "user": {
                "username": "housekeeping_hod",
                "first_name": "hod housekeeping",
                "last_name": "kempinski",
                "password": "housekeeping_hod",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            # "department": {
            #     "name": self.housekeeping_dpt.name,
            # },
            "department": f"{self.housekeeping_dpt.name}",
            "roles": [
                # {
                #     "role": {"name": self.supervisor.name},
                #     "is_active": True,
                # }
                self.supervisor.name
            ],
            # "gender": {"name": self.female.name},
            "gender": f"{self.female.name}",
        }
        self.hk_hod = api_models.CustomUser.objects.create_user(
            **self.housekeeping_hod_user_data.get("user")
        )
        self.hk_hod_profile = api_models.Profile.objects.create(
            user=self.hk_hod, department=self.housekeeping_dpt
        )
        self.hk_hod_profile_role = api_models.ProfileRole.objects.create(
            profile=self.hk_hod_profile, role=self.supervisor, is_active=True
        )

        self.housekeeping_staff_member_data = {
            "user": {
                "username": "housekeeping_staff",
                "first_name": "staff housekeeping",
                "last_name": "kempinski",
                "password": "housekeeping_staff",
            },
            "residential_address": "John Doe Street.",
            "email": "test.user@domain.com",
            "department": {
                "name": self.housekeeping_dpt.name,
            },
            "roles": [
                {
                    "role": {"name": self.staff.name},
                    "is_active": True,
                }
            ],
            "gender": {"name": self.female.name},
        }
        self.hk_staff = api_models.CustomUser.objects.create_user(
            **self.housekeeping_staff_member_data.get("user")
        )
        self.hk_staff_profile = api_models.Profile.objects.create(
            user=self.hk_staff, department=self.housekeeping_dpt
        )
        self.hk_hod_profile_role = api_models.ProfileRole.objects.create(
            profile=self.hk_staff_profile, role=self.staff, is_active=True
        )

        # get access token for system user
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)

        # send a post request to create hk staff member profile
        REGISTER_URL = reverse("register")
        self.client.post(
            REGISTER_URL,
            data=self.housekeeping_staff_member_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )

    def test_register_url(self):
        register_url = reverse("register")
        self.assertEqual(register_url, "/koms/accounts/register/")

    def test_register_new_user(self):
        REGISTER_URL = reverse("register")
        response = self.client.post(
            REGISTER_URL,
            data=self.new_user_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(f"response.data {response.data}")
        self.assertEqual(response.status_code, 201)
        self.assertIn("full_name", response.data)
        self.assertEqual(
            response.data["full_name"],
            f"{self.housekeeping_hod_user_data.get('user').get('first_name')} {self.housekeeping_hod_user_data.get('user').get('last_name')}",
        )

    def test_logout_url(self):
        logout_url = reverse("logout")
        self.assertEqual(logout_url, "/koms/accounts/logout/")

    def test_logout(self):
        logout_url = reverse("logout")
        # print(f'Refresh token: {self.refresh.token}')
        response = self.client.post(
            logout_url,
            data={"refresh_token": str(self.refresh)},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        # print(f'Response Content: {response.json()}')
        self.assertEqual(response.status_code, 205)

    def test_logout_without_refresh_token(self):
        logout_url = reverse("logout")
        response = self.client.post(
            logout_url,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_change_password_url(self):
        change_password_url = reverse("change_password")
        self.assertEqual(change_password_url, "/koms/accounts/change-password/")

    def test_change_password(self):
        change_password_url = reverse("change_password")
        response = self.client.post(
            change_password_url,
            data={"new_password": "new_user_password"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 200)

    def test_change_password_with_empty_password(self):
        change_password_url = reverse("change_password")
        response = self.client.post(
            change_password_url,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        self.assertEqual(response.status_code, 400)

    def test_reset_password_url(self):
        self.assertEqual("/koms/accounts/reset-password/", reverse("reset_password"))

    def test_reset_password(self):
        reset_password_url = reverse("reset_password")
        response = self.client.post(
            path=reset_password_url,
            content_type="application/json",
            data={"username": "system_user", "reset_channel": "email"},
        )
        print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 201)

    def test_reset_password_with_invalid_username(self):
        reset_password_url = reverse("reset_password")
        response = self.client.post(
            path=reset_password_url,
            content_type="application/json",
            data={"username": "system_test_user_1", "reset_channel": "email"},
        )
        # print(f'Response: {response.json()}')
        self.assertEqual(response.status_code, 400)

    def test_profile_shift_assign_url(self):
        assign_profile_shift_url = reverse("assign_shift")
        self.assertEqual(assign_profile_shift_url, "/koms/shift-management/")

    def test_profile_shift_assign(self):
        assign_profile_shift_url = reverse("assign_shift")
        # hk_hod = api_models.CustomUser.objects.get(username='housekeeping_hod')
        profile = api_models.Profile.objects.get(user__username="housekeeping_staff")
        shift = api_models.Shift.objects.get(name__iexact="morning")
        refresh = RefreshToken.for_user(self.hk_hod)
        access_token = str(refresh.access_token)
        response = self.client.post(
            path=assign_profile_shift_url,
            data={
                "profile": profile.id,
                "shift": shift.id,
                "date": datetime.date.today(),
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 201)

    def test_profile_shift_assign_with_different_dept(self):
        assign_profile_shift_url = reverse("assign_shift")
        # hk_hod = api_models.CustomUser.objects.get(username='housekeeping_hod')
        profile = api_models.Profile.objects.get(user__username="housekeeping_staff")
        shift = api_models.Shift.objects.get(name__iexact="morning")
        response = self.client.post(
            path=assign_profile_shift_url,
            data={
                "profile": profile.id,
                "shift": shift.id,
                "date": datetime.date.today(),
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 400)

    def test_profile_shift_assign_with_incorrect_user_role(self):
        assign_profile_shift_url = reverse("assign_shift")
        # hk_hod = api_models.CustomUser.objects.get(username='housekeeping_hod')
        profile = api_models.Profile.objects.get(user__username="housekeeping_staff")
        # print(profile.roles.exclude(role__name__iexact('')))
        shift = api_models.Shift.objects.get(name__iexact="morning")
        refresh = RefreshToken.for_user(self.hk_staff)
        access_token = str(refresh.access_token)
        response = self.client.post(
            path=assign_profile_shift_url,
            data={
                "profile": profile.id,
                "shift": shift.id,
                "date": datetime.date.today(),
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 400)

    def test_edit_user_profile(self):
        pass

    def test_assign_shift_with_wrong_user_account(self):
        pass


class ShiftAssignmentTest(TestCase):
    def setUpTestData(self):
        pass

    def setUp(self):
        pass


class HouseKeepingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.housekeeping_supervisor_data = {
            "username": "housekeeping_supervisor",
            "first_name": "House-Keeping Supervisor",
            "last_name": "Kempinski",
            "password": "housekeeping_supervisor",
        }
        cls.housekeeping_staff_data = {
            "username": "housekeeping_staff",
            "first_name": "House-Keeping Staff",
            "last_name": "Kempinski",
            "password": "housekeeping_staff",
        }
        cls.department_names = ["General", "House Keeping"]
        cls.role_names = ["Supervisor", "Staff Member"]
        cls.room_category_names = ["Suite", "Room"]
        cls.room_type_names = ["Deluxe", "Presidential"]
        cls.hotel_view_names = ["Pool", "City"]
        cls.gender_names = ["Female", "Male"]
        cls.hotel_floor_names = ["First Floor", "Second Floor", "Third Floor"]
        cls.shift_names = ["Morning Shift", "Afternoon Shift", "Evening Shift"]
        cls.house_keeping_state_names = [
            "waiting",
            "used",
            "assigned",
            "cleaned",
            "IP",
            "faulty",
        ]
        api_models.Department.objects.bulk_create(
            [api_models.Department(name=name) for name in cls.department_names]
        )
        api_models.Role.objects.bulk_create(
            [api_models.Role(name=name) for name in cls.role_names]
        )
        api_models.RoomCategory.objects.bulk_create(
            [api_models.RoomCategory(name=name) for name in cls.room_category_names]
        )

        api_models.HotelView.objects.bulk_create(
            [api_models.HotelView(name=name) for name in cls.hotel_view_names]
        )
        api_models.HotelFloor.objects.bulk_create(
            [api_models.HotelFloor(name=name) for name in cls.hotel_floor_names]
        )
        api_models.Shift.objects.bulk_create(
            [api_models.Shift(name=name) for name in cls.shift_names]
        )
        api_models.Gender.objects.bulk_create(
            [api_models.Gender(name=name) for name in cls.gender_names]
        )
        api_models.HouseKeepingState.objects.bulk_create(
            [
                api_models.HouseKeepingState(name=name)
                for name in cls.house_keeping_state_names
            ]
        )

    def setUp(self):
        departments = api_models.Department.objects.all()
        roles = api_models.Role.objects.all()
        room_categories = api_models.RoomCategory.objects.all()
        house_keeping_states = api_models.HouseKeepingState.objects.all()
        genders = api_models.Gender.objects.all()
        floors = api_models.HotelFloor.objects.all()
        shifts = api_models.Shift.objects.all()
        morning_shift = shifts.get(name__iexact="morning shift")
        afternoon_shift = shifts.get(name__iexact="afternoon shift")
        evening_shift = shifts.get(name__iexact="evening shift")
        first_floor = floors.get(name__iexact="first floor")
        second_floor = floors.get(name__iexact="second floor")
        third_floor = floors.get(name__iexact="third floor")
        male = genders.get(name__iexact="male")
        female = genders.get(name__iexact="female")
        suite_category = room_categories.get(name__iexact="suite")
        normal_room_category = room_categories.get(name__iexact="room")
        hotel_views = api_models.HotelView.objects.all()
        city_view = hotel_views.get(name__iexact="city")
        pool_view = hotel_views.get(name__iexact="pool")
        house_keeping_dpt = departments.get(name__iexact="house keeping")
        general_dpt = departments.get(name__iexact="general")
        supervisor_role = roles.get(name__iexact="supervisor")
        staff_member_role = roles.get(name__iexact="staff member")
        self.house_keeping_state_waiting = house_keeping_states.get(
            name__iexact="waiting"
        )
        self.house_keeping_state_used = house_keeping_states.get(name__iexact="used")
        self.house_keeping_state_assigned = house_keeping_states.get(
            name__iexact="assigned"
        )
        self.house_keeping_state_cleaned = house_keeping_states.get(
            name__iexact="cleaned"
        )
        self.house_keeping_state_ip = house_keeping_states.get(name__iexact="ip")
        self.house_keeping_state_faulty = house_keeping_states.get(
            name__iexact="faulty"
        )
        api_models.RoomType.objects.bulk_create(
            [
                api_models.RoomType(
                    name=name,
                    room_category=suite_category,
                    max_guests=3,
                    bed="King Size",
                    view=city_view,
                    price_per_night=1000,
                )
                for name in self.room_type_names
            ]
        )
        api_models.HouseKeepingStateTrans.objects.bulk_create(
            [
                api_models.HouseKeepingStateTrans(
                    name="waiting-to-assigned",
                    initial_trans_state=self.house_keeping_state_waiting,
                    final_trans_state=self.house_keeping_state_assigned,
                ),
                api_models.HouseKeepingStateTrans(
                    name="assigned-to-cleaned",
                    initial_trans_state=self.house_keeping_state_assigned,
                    final_trans_state=self.house_keeping_state_cleaned,
                ),
                api_models.HouseKeepingStateTrans(
                    name="assigned-to-faulty",
                    initial_trans_state=self.house_keeping_state_assigned,
                    final_trans_state=self.house_keeping_state_faulty,
                ),
                api_models.HouseKeepingStateTrans(
                    name="cleaned-to-ip",
                    initial_trans_state=self.house_keeping_state_cleaned,
                    final_trans_state=self.house_keeping_state_ip,
                ),
                api_models.HouseKeepingStateTrans(
                    name="ip-to-used",
                    initial_trans_state=self.house_keeping_state_ip,
                    final_trans_state=self.house_keeping_state_used,
                ),
                api_models.HouseKeepingStateTrans(
                    name="used-to-waiting",
                    initial_trans_state=self.house_keeping_state_used,
                    final_trans_state=self.house_keeping_state_assigned,
                ),
            ]
        )

        # Create user accounts for house-keeping supervisor and staff
        self.housekeeping_supervisor_account = (
            api_models.CustomUser.objects.create_user(
                **self.housekeeping_supervisor_data
            )
        )
        self.housekeeping_staff_account = api_models.CustomUser.objects.create_user(
            **self.housekeeping_staff_data
        )
        # Create profiles for house-keeping supervisor and staff
        self.housekeeping_supervisor_profile = api_models.Profile.objects.create(
            full_name=f"{self.housekeeping_supervisor_account.first_name} {self.housekeeping_supervisor_account.last_name}",
            user=self.housekeeping_supervisor_account,
            department=house_keeping_dpt,
            gender=male,
        )
        self.housekeeping_staff_profile = api_models.Profile.objects.create(
            full_name=f"{self.housekeeping_staff_account.first_name} {self.housekeeping_staff_account.last_name}",
            user=self.housekeeping_staff_account,
            department=house_keeping_dpt,
            gender=male,
        )
        # assign roles to house-keeping supervisor and staff
        api_models.ProfileRole.objects.bulk_create(
            [
                api_models.ProfileRole(
                    profile=self.housekeeping_supervisor_profile,
                    role=supervisor_role,
                    is_active=True,
                ),
                api_models.ProfileRole(
                    profile=self.housekeeping_staff_profile,
                    role=staff_member_role,
                    is_active=True,
                ),
            ]
        )
        # Create rooms
        room_types = api_models.RoomType.objects.all()
        presidential = room_types.get(name__iexact="presidential")
        deluxe = room_types.get(name__iexact="deluxe")
        room_numbers = ["RM001", "RM002", "RM003", "RM004", "RM005", "RM006"]
        api_models.Room.objects.bulk_create(
            [
                api_models.Room(
                    room_number=room_number,
                    floor=first_floor,
                    room_type=deluxe,
                    price_per_night=1000.00,
                    is_occupied=False,
                )
                for room_number in room_numbers
            ]
        )
        last_room = api_models.Room.objects.last()
        # Get refresh and access token for house-keeping supervisor
        self.housekeeping_supervisor_refresh = RefreshToken.for_user(
            user=self.housekeeping_supervisor_account
        )
        self.housekeeping_supervisor_access_token = str(
            self.housekeeping_supervisor_refresh.access_token
        )
        self.housekeeping_staff_refresh = RefreshToken.for_user(
            user=self.housekeeping_staff_account
        )
        self.housekeeping_staff_access_token = str(
            self.housekeeping_staff_refresh.access_token
        )

        self.house_keeping_assignment_data = {
            "shift": morning_shift.name,
            "room": last_room.room_number,
            "assignment_date": datetime.date.today(),
            "assigned_to": self.housekeeping_staff_profile.id,
        }

        # assign house-keeping staff to a shift
        api_models.ProfileShiftAssign.objects.create(
            department=house_keeping_dpt,
            profile=self.housekeeping_staff_profile,
            shift=morning_shift,
            date=datetime.date(2024, 12, 28),
        )

        self.room_keeping_assign = api_models.RoomKeepingAssign.objects.create(
            room=last_room,
            shift=morning_shift,
            assignment_date=datetime.date(2024, 12, 28),
            assigned_to=self.housekeeping_supervisor_profile,
            created_by=self.housekeeping_supervisor_profile,
        )

    def test_house_keeping_assignment_url(self):
        self.assertEqual("/koms/house-keeping/assign/", reverse("assign_house_keeping"))

    def test_house_keeping_assignment(self):
        url = reverse("assign_house_keeping")
        response = self.client.post(
            url,
            data=self.house_keeping_assignment_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.housekeeping_supervisor_access_token}",
        )
        print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 201)

    # def test_house_keeping_assignment_edit(self):
    #     room_keeping_task_shift = api_models.Shift.objects.get(
    #         name=self.house_keeping_assignment_data.get('shift'),
    #     )
    #     room_keeping_task_room = api_models.Room.objects.get(
    #         room_number=self.house_keeping_assignment_data.get('room')
    #     )
    #     room_keeping_task_assigned_to = api_models.Profile.objects.get(
    #         id=self.house_keeping_assignment_data.get('assigned_to')
    #     )
    #     room_keeping_task_date = self.house_keeping_assignment_data.get('assignment_date')
    #     room_keeping_task = api_models.RoomKeepingAssign.objects.get(
    #         assigned_to=room_keeping_task_assigned_to,
    #         shift=room_keeping_task_shift,
    #         assignment_date=room_keeping_task_date,
    #         room=room_keeping_task_room
    #     )
    #     url = reverse("assign_house_keeping", kwargs={'pk': room_keeping_task.id})
    #     data=self.house_keeping_assignment_data
    #     data['assignment_date'] = datetime.date(2025, 1, 1)
    #     response = self.client.put(
    #         url,
    #         data=data,
    #         content_type="application/json",
    #         HTTP_AUTHORIZATION=f"Bearer {self.housekeeping_supervisor_access_token}",
    #     )
    #     print(f"Response: {response.json()}")
    #     self.assertEqual(response.status_code, 201)

    def test_process_room_keeping_url(self):
        self.assertEqual("/koms/house-keeping/process/", reverse("process_roomkeeping"))

    def test_process_room_keeping(self):
        url = reverse("process_roomkeeping")
        data = {
            "room_keeping_assign": self.room_keeping_assign.id,
            "room_state_trans": "cleaned-to-ip",
            # "room_state_trans": "assigned-to-faulty",
            # "room_state_trans": "assigned-to-cleaned",
            # "room_state_trans": assigned_to_cleaned.id,
            "date_processed": self.room_keeping_assign.date_created,
            "note": "",
        }
        response = self.client.post(
            path=url,
            data=data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.housekeeping_supervisor_access_token}",
        )
        print(response.json())
        self.assertEqual(response.status_code, 201)


class BookingTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.frontdesk_supervisor_data = {
            "username": "frontdesk_supervisor",
            "first_name": "FrontDesk Supervisor",
            "last_name": "Kempinski",
            "password": "frontdesk_supervisor",
        }
        cls.frontdesk_staff_data = {
            "username": "frontdesk_staff",
            "first_name": "FrontDesk Staff",
            "last_name": "Kempinski",
            "password": "frontdesk_staff",
        }
        cls.department_names = ["General", "House Keeping", "FrontDesk"]
        cls.role_names = ["Supervisor", "Staff Member"]
        cls.room_category_names = ["Suite", "Room"]
        cls.room_type_names = ["Deluxe", "Presidential"]
        cls.hotel_view_names = ["Pool", "City"]
        cls.gender_names = ["Female", "Male"]
        cls.hotel_floor_names = ["First Floor", "Second Floor", "Third Floor"]
        cls.shift_names = ["Morning Shift", "Afternoon Shift", "Evening Shift"]
        cls.sponsor_type_names = ["Self", "Coorporate", "Group", "State"]
        cls.payment_type_names = ["Self", "Credit"]
        cls.title_names = ["-", "Mr.", "Mrs.", "Miss"]
        api_models.Department.objects.bulk_create(
            [api_models.Department(name=name) for name in cls.department_names]
        )
        api_models.Role.objects.bulk_create(
            [api_models.Role(name=name) for name in cls.role_names]
        )
        api_models.RoomCategory.objects.bulk_create(
            [api_models.RoomCategory(name=name) for name in cls.room_category_names]
        )

        api_models.HotelView.objects.bulk_create(
            [api_models.HotelView(name=name) for name in cls.hotel_view_names]
        )
        api_models.HotelFloor.objects.bulk_create(
            [api_models.HotelFloor(name=name) for name in cls.hotel_floor_names]
        )
        api_models.Shift.objects.bulk_create(
            [api_models.Shift(name=name) for name in cls.shift_names]
        )
        api_models.Gender.objects.bulk_create(
            [api_models.Gender(name=name) for name in cls.gender_names]
        )
        api_models.SponsorType.objects.bulk_create(
            [api_models.SponsorType(name=name) for name in cls.sponsor_type_names]
        )
        api_models.PaymentType.objects.bulk_create(
            [api_models.PaymentType(name=name) for name in cls.payment_type_names]
        )
        api_models.NameTitle.objects.bulk_create(
            [api_models.NameTitle(name=name) for name in cls.title_names]
        )

    def setUp(self):
        departments = api_models.Department.objects.all()
        roles = api_models.Role.objects.all()
        room_categories = api_models.RoomCategory.objects.all()
        house_keeping_states = api_models.HouseKeepingState.objects.all()
        genders = api_models.Gender.objects.all()
        floors = api_models.HotelFloor.objects.all()
        shifts = api_models.Shift.objects.all()
        morning_shift = shifts.get(name__iexact="morning shift")
        afternoon_shift = shifts.get(name__iexact="afternoon shift")
        evening_shift = shifts.get(name__iexact="evening shift")
        first_floor = floors.get(name__iexact="first floor")
        second_floor = floors.get(name__iexact="second floor")
        third_floor = floors.get(name__iexact="third floor")
        male = genders.get(name__iexact="male")
        female = genders.get(name__iexact="female")
        suite_category = room_categories.get(name__iexact="suite")
        normal_room_category = room_categories.get(name__iexact="room")
        hotel_views = api_models.HotelView.objects.all()
        city_view = hotel_views.get(name__iexact="city")
        pool_view = hotel_views.get(name__iexact="pool")
        frontdesk_dpt = departments.get(name__iexact="frontdesk")
        general_dpt = departments.get(name__iexact="general")
        supervisor_role = roles.get(name__iexact="supervisor")
        staff_member_role = roles.get(name__iexact="staff member")
        api_models.RoomType.objects.bulk_create(
            [
                api_models.RoomType(
                    name=name,
                    room_category=suite_category,
                    max_guests=3,
                    bed="King Size",
                    view=city_view,
                    price_per_night=1000,
                )
                for name in self.room_type_names
            ]
        )

        # create frontdesk staff and supervisor user accounts
        self.frontdesk_supervisor_account = api_models.CustomUser.objects.create_user(
            **self.frontdesk_supervisor_data
        )
        self.frontdesk_staff_account = api_models.CustomUser.objects.create_user(
            **self.frontdesk_staff_data
        )

        # create frontdesk staff and supervisor profiles
        self.frontdesk_supervisor_profile = api_models.Profile.objects.create(
            full_name=f"{self.frontdesk_supervisor_account.first_name} {self.frontdesk_supervisor_account.last_name}",
            user=self.frontdesk_supervisor_account,
            department=frontdesk_dpt,
            gender=male,
        )
        self.frontdesk_staff_profile = api_models.Profile.objects.create(
            full_name=f"{self.frontdesk_staff_account.first_name} {self.frontdesk_staff_account.last_name}",
            user=self.frontdesk_staff_account,
            department=frontdesk_dpt,
            gender=male,
        )
        # assign roles to house-keeping supervisor and staff
        api_models.ProfileRole.objects.bulk_create(
            [
                api_models.ProfileRole(
                    profile=self.frontdesk_supervisor_profile,
                    role=supervisor_role,
                    is_active=True,
                ),
                api_models.ProfileRole(
                    profile=self.frontdesk_staff_profile,
                    role=staff_member_role,
                    is_active=True,
                ),
            ]
        )
        # Create rooms
        room_types = api_models.RoomType.objects.all()
        presidential = room_types.get(name__iexact="presidential")
        deluxe = room_types.get(name__iexact="deluxe")
        room_numbers = ["RM001", "RM002", "RM003", "RM004", "RM005", "RM006"]
        api_models.Room.objects.bulk_create(
            [
                api_models.Room(
                    room_number=room_number,
                    floor=first_floor,
                    room_type=deluxe,
                    price_per_night=1000.00,
                    is_occupied=False,
                    max_guests=3,
                    room_maintenance_status="cleaned",
                    room_booking_status="empty",
                )
                for room_number in room_numbers
            ]
        )
        self.last_room = api_models.Room.objects.last()

        # Get refresh and access token for frontdesk supervisor and staff
        self.frontdesk_supervisor_refresh = RefreshToken.for_user(
            user=self.frontdesk_supervisor_account
        )
        self.frontdesk_supervisor_access_token = str(
            self.frontdesk_supervisor_refresh.access_token
        )
        self.frontdesk_staff_refresh = RefreshToken.for_user(
            user=self.frontdesk_staff_account
        )
        self.frontdesk_staff_access_token = str(
            self.frontdesk_staff_refresh.access_token
        )

        # assign frontdesk staff to a shift
        api_models.ProfileShiftAssign.objects.create(
            department=frontdesk_dpt,
            profile=self.frontdesk_staff_profile,
            shift=morning_shift,
            date=datetime.date(2024, 12, 30),
        )
        # create sponsor types
        self.self_sponsor_type = api_models.SponsorType.objects.get(name__iexact="self")
        self.corp_sponsor_type = api_models.SponsorType.objects.get(
            name__iexact="coorporate"
        )

        # create self sponsor and Spagad coorporate sponsor
        self.self_sponsor = api_models.Sponsor.objects.create(
            name="Self", sponsor_type=self.self_sponsor_type
        )
        self.corp_sponsor = api_models.Sponsor.objects.create(
            name="Spagad Tech", sponsor_type=self.corp_sponsor_type
        )

        self.booking_data = {
            "title": "Mr.",
            "first_name": "Selassie",
            "last_name": "Awagah",
            "gender": "Male",
            "room": self.last_room.room_number,
            "check_in": "2024-12-30",
            "check_out": "2025-01-03",
            "number_of_older_guests": 1,
            "number_of_younger_guests": 0,
            "rate_type": "non-member",
            "rate": 4000.00,
            "sponsor": self.self_sponsor.id,
        }

        self.receipt = api_models.Receipt.objects.create(
            issued_to=f"{self.booking_data.get('title')} {self.booking_data.get('first_name')} {self.booking_data.get('last_name')}",
            gender=male,
            receipt_number='R00000001',
            amount_paid=10000,
            amount_available=10000,
            date_issued=datetime.date(2024, 12, 29),
        )

        self.booking_data['receipt'] = self.receipt.receipt_number

        self.booking = api_models.Booking.objects.create(
            first_name="Selassie",
            last_name="Awagah",
            room=self.last_room,
            check_in=datetime.date(2024, 12, 30),
            check_out=datetime.date(2025, 1, 3),
            number_of_older_guests=1,
            number_of_younger_guests=0,
            rate_type="non-member",
            rate=4000.00,
            sponsor=self.self_sponsor,
        )

    def test_booking_url(self):
        self.assertEqual(reverse("bookings"), "/koms/bookings/")

    def test_booking_get(self):
        url = reverse("bookings")
        response = self.client.get(
            path=url, HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}"
        )
        self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.json(), [])

    def test_booking_self_sponsor(self):
        url = reverse("bookings")
        response = self.client.post(
            path=url,
            data=self.booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 201)
    
    def test_booking_self_sponsor_insufficient_receipt_balance(self):
        url = reverse("bookings")
        receipt = self.receipt
        receipt.amount_available = self.booking_data.get('rate') - 1
        receipt.save()
        self.booking_data['receipt'] = receipt.receipt_number
        response = self.client.post(
            path=url,
            data=self.booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)
    
    def test_booking_with_credit_sponsor(self):
        url = reverse("bookings")
        booking_data = self.booking_data
        booking_data['sponsor'] = self.corp_sponsor.id
        booking_data['receipt'] = ''
        response = self.client.post(
            path=url,
            data=self.booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 201)

    def test_booking_with_invalid_sponsor(self):
            url = reverse("bookings")
            booking_data = self.booking_data
            booking_data['sponsor'] = 9999  # Invalid sponsor ID
            response = self.client.post(
                path=url,
                data=booking_data,
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
            )
            # print(f"Response: {response.json()}")
            self.assertEqual(response.status_code, 400)

    def test_booking_with_invalid_room(self):
        url = reverse("bookings")
        booking_data = self.booking_data
        booking_data['room'] = 'INVALID_ROOM'  # Invalid room number
        response = self.client.post(
            path=url,
            data=booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)

    def test_booking_with_missing_fields(self):
        url = reverse("bookings")
        booking_data = self.booking_data
        del booking_data['first_name']  # Remove required field
        response = self.client.post(
            path=url,
            data=booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)

    def test_booking_with_invalid_date_range(self):
        url = reverse("bookings")
        booking_data = self.booking_data
        booking_data['check_in'] = "2025-01-03"
        booking_data['check_out'] = "2024-12-30"  # Invalid date range
        response = self.client.post(
            path=url,
            data=booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)

    def test_booking_with_invalid_rate_type(self):
        url = reverse("bookings")
        booking_data = self.booking_data
        booking_data['rate_type'] = "INVALID_RATE_TYPE"  # Invalid rate type
        response = self.client.post(
            path=url,
            data=booking_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 400)

    def test_booking_details_url(self):
        self.assertEqual(f"/koms/bookings/{self.booking.id}/", reverse("booking_details", kwargs={'pk': self.booking.id}))

    def test_booking_details(self):
        url = reverse("booking_details", kwargs={'pk': self.booking.id})
        response = self.client.get(
            path=url, HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}"
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_booking_extend(self):
        url = reverse("extend_booking")
        extend_data = {
            'booking_id': self.booking.id,
            'num_days': 2,
        }
        response = self.client.post(
            path=url,
            data=extend_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        # print(f"Response: {response.json()}")
        self.assertEqual(response.status_code, 200)

    def test_booking_checkout(self):
        url = reverse("checkout_booking")
        checkout_data = {
            'booking_id': self.booking.id,
        }
        response = self.client.post(
            path=url,
            data=checkout_data,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.frontdesk_staff_access_token}",
        )
        print(f"Checkout Test Response: {response.json()}")
        self.assertEqual(response.status_code, 200)

