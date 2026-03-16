"""Custom User model for Medilink platform.

Includes:
- Email-based authentication
- Role and account status management
- Login tracking and brute-force protection helpers
"""
from datetime import timedelta

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

from common.enums import UserRole, UserAccountStatus


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.ADMIN)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model using email as the unique identifier.
    
    Fields:
        email: Unique email address (used for login)
        role: User role (PATIENT, PROVIDER, ADMIN)
        is_active: Whether the account is active
        is_staff: Whether user can access admin site
        is_superuser: Whether user has all permissions
        created_at: Account creation timestamp
    """
    email = models.EmailField(
        unique=True,
        db_index=True,
        help_text='Email address used for login'
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.PATIENT,
        db_index=True,
        help_text='User role in the system'
    )
    account_status = models.CharField(
        max_length=20,
        choices=UserAccountStatus.choices,
        default=UserAccountStatus.ACTIVE,
        db_index=True,
        help_text='Account status (ACTIVE, SUSPENDED, DEACTIVATED)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Designates whether this user can log in (Django built-in)'
    )
    is_staff = models.BooleanField(
        default=False,
        help_text='Designates whether the user can log into admin site'
    )
    is_superuser = models.BooleanField(
        default=False,
        help_text='Designates that this user has all permissions'
    )
    # Email verification
    email_verified = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether email address has been verified'
    )
    email_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When email was verified'
    )
    
    # Patient identity fields (stored on User for simplicity)
    first_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='First name (primarily for patients)'
    )
    last_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Last name (primarily for patients)'
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        help_text='Phone number'
    )
    profile_image = models.ImageField(
        upload_to='users/profiles/',
        null=True,
        blank=True,
        help_text='Profile image for account users'
    )
    
    # Login tracking
    last_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last login timestamp (Django built-in, but we track it explicitly)'
    )
    last_login_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='IP address of last login'
    )
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text='Number of consecutive failed login attempts'
    )
    locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Account locked until this time (for brute force protection)'
    )
    
    # Profile completion tracking
    profile_completed = models.BooleanField(
        default=False,
        db_index=True,
        help_text='Whether user profile is complete'
    )
    profile_completion_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Profile completion percentage (0-100)'
    )
    
    # Audit fields
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text='Account creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='Last update timestamp'
    )
    created_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_users',
        help_text='User who created this account (for admin-created accounts)'
    )
    updated_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_users',
        help_text='User who last updated this account'
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Email is the only required field
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['account_status']),
            models.Index(fields=['is_active']),
            models.Index(fields=['email_verified']),
            models.Index(fields=['profile_completed']),
            models.Index(fields=['locked_until']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the user's full name if available, otherwise email."""
        if self.first_name and self.last_name:
            return f'{self.first_name} {self.last_name}'
        if self.first_name:
            return self.first_name
        return self.email
    
    def get_short_name(self):
        """Return the user's first name if available, otherwise email."""
        return self.first_name if self.first_name else self.email
    
    @property
    def is_patient(self):
        """Check if user is a patient."""
        return self.role == UserRole.PATIENT
    
    @property
    def is_provider(self):
        """Check if user is a provider."""
        return self.role == UserRole.PROVIDER
    
    @property
    def is_admin(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    @property
    def can_login(self):
        """
        Check if user can login based on account status.
        Combines account_status and is_active checks.
        """
        return (
            self.is_active and
            self.account_status == UserAccountStatus.ACTIVE
        )
    
    def suspend(self):
        """Suspend the user account."""
        self.account_status = UserAccountStatus.SUSPENDED
        self.is_active = False
        self.save(update_fields=['account_status', 'is_active'])
    
    def deactivate(self):
        """Deactivate the user account."""
        self.account_status = UserAccountStatus.DEACTIVATED
        self.is_active = False
        self.save(update_fields=['account_status', 'is_active'])
    
    def activate(self):
        """Activate the user account."""
        self.account_status = UserAccountStatus.ACTIVE
        self.is_active = True
        self.save(update_fields=['account_status', 'is_active'])

    # ------------------------------------------------------------------
    # Profile completion helpers
    # ------------------------------------------------------------------

    def recalculate_profile_completion(self) -> None:
        """Recalculate and persist profile completion percentage.

        This is a heuristic based on key fields for each role. It is
        intentionally simple and focuses on the most important pieces of
        information (identity + core professional documents).
        """
        completed = 0
        total = 0

        def add(condition: bool) -> None:
            nonlocal completed, total
            total += 1
            if condition:
                completed += 1

        # Base signal: email verified improves completion
        add(self.email_verified)

        # Patient-specific completion
        if self.is_patient:
            # Core identity fields for patients
            add(bool(self.first_name))
            add(bool(self.last_name))
            add(bool(self.phone_number))
            
            # Check for linked patient record (provides medical info)
            try:
                if hasattr(self, 'patient_record') and self.patient_record:
                    patient_record = self.patient_record
                    add(bool(patient_record.date_of_birth))
                    add(bool(patient_record.gender))
                    # Having a linked patient record is a strong signal
                    add(True)
            except Exception:
                pass
            
            # Check for at least one address
            try:
                from django.contrib.contenttypes.models import ContentType
                from address.models import Address
                user_content_type = ContentType.objects.get_for_model(self.__class__)
                has_address = Address.objects.filter(
                    content_type=user_content_type,
                    object_id=self.id
                ).exists()
                add(has_address)
            except Exception:
                pass

        # Provider-specific completion based on subtype
        elif self.is_provider:
            try:
                provider = self.provider_profile
            except Exception:
                provider = None

            if provider is not None:
                provider_type = getattr(provider, 'provider_type', None)

                try:
                    if provider_type == 'DOCTOR' and hasattr(provider, 'doctor_profile'):
                        doctor = provider.doctor_profile
                        add(bool(doctor.first_name))
                        add(bool(doctor.last_name))
                        add(bool(doctor.license_number))
                        add(bool(doctor.degree_document))
                        add(bool(doctor.profile_image))

                    elif provider_type == 'NURSE' and hasattr(provider, 'nurse_profile'):
                        nurse = provider.nurse_profile
                        add(bool(nurse.first_name))
                        add(bool(nurse.last_name))
                        add(bool(nurse.license_number))
                        add(bool(nurse.degree_document))
                        add(bool(nurse.entrepreneur_card_front))
                        add(bool(nurse.entrepreneur_card_back))

                    elif provider_type == 'CLINIC' and hasattr(provider, 'clinic_profile'):
                        clinic = provider.clinic_profile
                        add(bool(clinic.clinic_name))
                        add(bool(clinic.license_number))
                        add(bool(clinic.phone_number))
                        add(bool(clinic.license_document))

                    elif provider_type == 'LABORATORY' and hasattr(provider, 'laboratory_profile'):
                        lab = provider.laboratory_profile
                        add(bool(lab.lab_name))
                        add(bool(lab.license_number))
                        add(bool(lab.phone_number))
                        add(bool(lab.license_document))

                    elif provider_type == 'SELLER' and hasattr(provider, 'seller_profile'):
                        seller = provider.seller_profile
                        add(bool(seller.business_name))
                        add(bool(seller.tax_id))
                        add(bool(seller.phone_number))
                        add(bool(seller.business_license))

                    elif provider_type == 'VTC' and hasattr(provider, 'vtc_profile'):
                        vtc = provider.vtc_profile
                        add(bool(vtc.company_name))
                        add(bool(vtc.license_number))
                        add(bool(vtc.phone_number))
                        add(bool(vtc.transport_license))
                except Exception:
                    # If anything goes wrong, fall back to whatever we
                    # have already counted instead of breaking the call.
                    pass

        # Simple percentage based on counted fields
        percentage = 0
        if total > 0:
            percentage = int(round((completed / total) * 100))

        self.profile_completion_percentage = max(0, min(100, percentage))
        self.profile_completed = self.profile_completion_percentage >= 80
        self.save(update_fields=['profile_completion_percentage', 'profile_completed'])

    # ------------------------------------------------------------------
    # Login tracking & brute-force protection helpers
    # ------------------------------------------------------------------

    def is_locked(self) -> bool:
        """Return True if the account is currently locked.

        Locking is time-based using the ``locked_until`` field. When the
        lock has expired, this method will transparently reset the
        ``failed_login_attempts`` and ``locked_until`` fields.
        """
        if not self.locked_until:
            return False

        now = timezone.now()
        if self.locked_until <= now:
            # Lock expired – reset counters
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['failed_login_attempts', 'locked_until'])
            return False

        return True

    def record_failed_login(self, max_attempts: int = 5, lock_minutes: int = 30) -> None:
        """Record a failed login attempt and lock the account if needed.

        Behaviour (as per documentation):
        - After ``max_attempts`` consecutive failures, the account is locked
          for ``lock_minutes`` minutes.
        - If a previous lock has expired, counters are reset before
          incrementing.
        """
        now = timezone.now()

        # If previous lock expired, clear it before counting this failure
        if self.locked_until and self.locked_until <= now:
            self.failed_login_attempts = 0
            self.locked_until = None

        self.failed_login_attempts += 1

        if self.failed_login_attempts >= max_attempts:
            self.locked_until = now + timedelta(minutes=lock_minutes)

        self.save(update_fields=['failed_login_attempts', 'locked_until'])

    def record_login(self, ip_address: str | None = None) -> None:
        """Record a successful login.

        - Updates ``last_login`` and ``last_login_ip``
        - Resets ``failed_login_attempts`` and clears any lock
        """
        self.last_login = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.failed_login_attempts = 0
        self.locked_until = None
        self.save(update_fields=['last_login', 'last_login_ip', 'failed_login_attempts', 'locked_until'])
