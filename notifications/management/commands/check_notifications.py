"""
Diagnostic command to validate the notifications system.

Run on the droplet:
    python manage.py check_notifications
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Diagnose notification system: compare DB schema vs Django model'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  NOTIFICATIONS SYSTEM DIAGNOSTIC")
        self.stdout.write("=" * 60)

        self._check_table_exists()
        self._check_columns()
        self._check_device_tokens()
        self._check_notifications_count()
        self._check_firebase()
        self._test_create_notification()

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("  DIAGNOSTIC COMPLETE")
        self.stdout.write("=" * 60 + "\n")

    def _check_table_exists(self):
        self.stdout.write("\n--- 1. TABLE EXISTENCE ---")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tablename FROM pg_tables WHERE tablename IN ('notifications', 'notifications_devicetoken')"
            )
            tables = [row[0] for row in cursor.fetchall()]

        if 'notifications' in tables:
            self.stdout.write(self.style.SUCCESS("  ✅ 'notifications' table exists"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ 'notifications' table MISSING"))

        if 'notifications_devicetoken' in tables:
            self.stdout.write(self.style.SUCCESS("  ✅ 'notifications_devicetoken' table exists"))
        else:
            self.stdout.write(self.style.ERROR("  ❌ 'notifications_devicetoken' table MISSING"))

    def _check_columns(self):
        self.stdout.write("\n--- 2. NOTIFICATIONS TABLE COLUMNS (actual DB) ---")
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_name = 'notifications' "
                "ORDER BY ordinal_position"
            )
            db_columns = cursor.fetchall()

        if not db_columns:
            self.stdout.write(self.style.ERROR("  ❌ No columns found — table may not exist"))
            return

        db_col_names = set()
        self.stdout.write("  DB columns:")
        for col_name, data_type, nullable, default in db_columns:
            db_col_names.add(col_name)
            self.stdout.write(f"    - {col_name:25s} {data_type:20s} nullable={nullable}  default={default}")

        # Check what Django model expects
        self.stdout.write("\n  Django model expects these DB columns:")
        from notifications.models import Notification
        model_columns = {}
        for field in Notification._meta.get_fields():
            if hasattr(field, 'column'):
                model_columns[field.column] = field.get_internal_type()
                self.stdout.write(f"    - {field.column:25s} (field: {field.name}, type: {field.get_internal_type()})")

        # Compare
        self.stdout.write("\n  Comparison:")
        model_col_names = set(model_columns.keys())
        
        missing_in_db = model_col_names - db_col_names
        extra_in_db = db_col_names - model_col_names
        matched = model_col_names & db_col_names

        for col in sorted(matched):
            self.stdout.write(self.style.SUCCESS(f"    ✅ {col} — matched"))
        for col in sorted(missing_in_db):
            self.stdout.write(self.style.ERROR(f"    ❌ {col} — in Django model but NOT in DB"))
        for col in sorted(extra_in_db):
            self.stdout.write(self.style.WARNING(f"    ⚠️  {col} — in DB but NOT in Django model"))

        if missing_in_db:
            self.stdout.write(self.style.ERROR(
                "\n  🚨 MISMATCH FOUND! Django will crash when querying. "
                "Fix the model to match the DB or add the missing columns."
            ))
        else:
            self.stdout.write(self.style.SUCCESS("\n  ✅ All model columns exist in DB"))

    def _check_device_tokens(self):
        self.stdout.write("\n--- 3. DEVICE TOKENS ---")
        from notifications.models import DeviceToken
        total = DeviceToken.objects.count()
        active = DeviceToken.objects.filter(is_active=True).count()
        self.stdout.write(f"  Total tokens: {total}")
        self.stdout.write(f"  Active tokens: {active}")
        
        if active > 0:
            self.stdout.write(self.style.SUCCESS("  ✅ Active device tokens exist"))
            # Show breakdown by user
            from django.db.models import Count
            by_user = DeviceToken.objects.filter(is_active=True).values(
                'user__email'
            ).annotate(count=Count('id')).order_by('-count')[:10]
            for entry in by_user:
                self.stdout.write(f"    - {entry['user__email']}: {entry['count']} token(s)")
        else:
            self.stdout.write(self.style.WARNING("  ⚠️  No active device tokens"))

    def _check_notifications_count(self):
        self.stdout.write("\n--- 4. NOTIFICATIONS COUNT (raw SQL) ---")
        with connection.cursor() as cursor:
            try:
                cursor.execute("SELECT COUNT(*) FROM notifications")
                count = cursor.fetchone()[0]
                self.stdout.write(f"  Total notifications in DB (raw SQL): {count}")
                if count > 0:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ {count} notifications exist"))
                    # Show latest 5
                    cursor.execute("SELECT id, title, created_at FROM notifications ORDER BY created_at DESC LIMIT 5")
                    for row in cursor.fetchall():
                        self.stdout.write(f"    - [{row[2]}] {row[0]} : {row[1]}")
                else:
                    self.stdout.write(self.style.WARNING("  ⚠️  No notifications in DB"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error querying notifications: {e}"))

        # Also try Django ORM
        self.stdout.write("\n  Notifications via Django ORM:")
        try:
            from notifications.models import Notification
            orm_count = Notification.objects.count()
            self.stdout.write(f"  ORM count: {orm_count}")
            if orm_count > 0:
                self.stdout.write(self.style.SUCCESS(f"  ✅ Django ORM can read notifications"))
            else:
                self.stdout.write(self.style.WARNING("  ⚠️  ORM returns 0 — possible schema mismatch"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Django ORM FAILED: {e}"))
            self.stdout.write(self.style.ERROR("     This confirms a model/DB column mismatch!"))

    def _check_firebase(self):
        self.stdout.write("\n--- 5. FIREBASE ---")
        try:
            import firebase_admin
            if firebase_admin._apps:
                self.stdout.write(self.style.SUCCESS("  ✅ Firebase Admin SDK initialized"))
            else:
                self.stdout.write(self.style.ERROR("  ❌ Firebase Admin SDK NOT initialized"))
        except ImportError:
            self.stdout.write(self.style.ERROR("  ❌ firebase_admin not installed"))

    def _test_create_notification(self):
        self.stdout.write("\n--- 6. TEST NOTIFICATION CREATE ---")
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Get the first superuser or any user
        user = User.objects.filter(is_superuser=True).first() or User.objects.first()
        if not user:
            self.stdout.write(self.style.WARNING("  ⚠️  No users in DB, skipping test"))
            return

        self.stdout.write(f"  Testing with user: {user.email}")
        
        try:
            from notifications.models import Notification, NotificationType
            notif = Notification.objects.create(
                recipient=user,
                title="[DIAGNOSTIC] Test Notification",
                body="This is a test from check_notifications command.",
                notification_type=NotificationType.GENERAL,
                data={"source": "diagnostic"},
                is_read=True,  # mark read so it doesn't pollute unread count
            )
            self.stdout.write(self.style.SUCCESS(f"  ✅ Notification created successfully! ID: {notif.id}"))
            # Clean up
            notif.delete()
            self.stdout.write(self.style.SUCCESS("  ✅ Notification deleted (cleanup)"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ FAILED to create notification: {e}"))
            self.stdout.write(self.style.ERROR("     This is the root cause — fix the model to match the DB!"))
