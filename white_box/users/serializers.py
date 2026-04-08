from rest_framework import serializers
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from datetime import timedelta
import random
from .models import User, EmailVerificationCode
from users.utils.email import email_verification_code


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=6) #write_only=True表示这个字段只用于输入，不会在序列化输出中显示，min_length=6表示密码最少需要6个字符
    password_confirm = serializers.CharField(write_only=True, min_length=6) #用于确认密码输入，write_only=True表示这个字段只用于输入，不会在序列化输出中显示，min_length=6表示密码最少需要6个字符

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm']

    def validate_username(self, value): #value是传入的用户名
        """Check if username already exists"""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Username already exists')
        return value

    def validate_email(self, value):
        """Check if email already exists"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already exists')
        return value

    def validate(self, data):
        """Validate that passwords match"""
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})
        return data

    def create(self, validated_data):
        """Create user with hashed password"""
        validated_data.pop('password_confirm') #从validated_data中移除password_confirm字段，因为它不需要保存到数据库中
        validated_data['password'] = make_password(validated_data['password'])
        return User.objects.create(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        """Validate credentials"""
        try:
            user = User.objects.get(username=data['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError('Username or password is incorrect')

        from django.contrib.auth.hashers import check_password
        if not check_password(data['password'], user.password):
            raise serializers.ValidationError('Username or password is incorrect')

        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')

        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    class Meta:
        model = User
        fields = ['user_id', 'username', 'email', 'avatar', 'bio', 'phone', 'created_at', 'is_active']
        read_only_fields = ['user_id', 'created_at']


class VerificationCodeRequestSerializer(serializers.Serializer):
    """Request serializer for sending email verification code."""

    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(
        choices=EmailVerificationCode.PURPOSE_CHOICES,
        required=False,
        default=EmailVerificationCode.PURPOSE_LOGIN,
    )

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        purpose = attrs['purpose']

        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError('User not found')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')

        throttle_limit = timezone.now() - timedelta(seconds=60)
        has_recent_code = EmailVerificationCode.objects.filter(
            email=email,
            purpose=purpose,
            created_at__gte=throttle_limit,
        ).exists()
        if has_recent_code:
            raise serializers.ValidationError('Please wait 60 seconds before requesting a new code')

        attrs['email'] = email
        attrs['user'] = user
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        purpose = validated_data['purpose']
        code = f"{random.randint(100000, 999999)}"
        now = timezone.now()

        EmailVerificationCode.objects.filter(
            email=email,
            purpose=purpose,
            used_at__isnull=True,
            expires_at__gt=now,
        ).update(used_at=now)

        EmailVerificationCode.objects.create(
            email=email,
            code_hash=make_password(code),
            purpose=purpose,
            expires_at=now + timedelta(minutes=5),
        )

        email_verification_code(email=email, code=code, purpose=purpose)
        return {'email': email, 'purpose': purpose}


class LoginWithVerificationCodeSerializer(serializers.Serializer):
    """Serializer for login by email + verification code."""

    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        code = attrs['code'].strip()
        now = timezone.now()

        verification = EmailVerificationCode.objects.filter(
            email=email,
            purpose=EmailVerificationCode.PURPOSE_LOGIN,
            used_at__isnull=True,
            expires_at__gt=now,
        ).order_by('-created_at').first()

        if verification is None:
            raise serializers.ValidationError('Verification code is invalid or expired')

        if verification.attempt_count >= 5:
            verification.used_at = now
            verification.save(update_fields=['used_at'])
            raise serializers.ValidationError('Too many failed attempts, please request a new code')

        if not check_password(code, verification.code_hash):
            verification.attempt_count += 1
            if verification.attempt_count >= 5:
                verification.used_at = now
                verification.save(update_fields=['attempt_count', 'used_at'])
            else:
                verification.save(update_fields=['attempt_count'])
            raise serializers.ValidationError('Verification code is invalid or expired')

        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError('User not found')
        if not user.is_active:
            raise serializers.ValidationError('Account is disabled')

        attrs['email'] = email
        attrs['user'] = user
        attrs['verification'] = verification
        return attrs

    def create(self, validated_data):
        verification = validated_data['verification']
        verification.used_at = timezone.now()
        verification.save(update_fields=['used_at'])
        return {'user': validated_data['user']}


class ForgetPasswordSerializer(serializers.Serializer):
    """Serializer for reset password using email verification code."""

    email = serializers.EmailField(required=True)
    code = serializers.CharField(required=True, min_length=6, max_length=6)
    new_password = serializers.CharField(required=True, min_length=6)
    password_confirm = serializers.CharField(required=True, min_length=6)

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        code = attrs['code'].strip()
        now = timezone.now()

        if attrs['new_password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password': 'Passwords do not match'})

        verification = EmailVerificationCode.objects.filter(
            email=email,
            purpose=EmailVerificationCode.PURPOSE_RESET_PASSWORD,
            used_at__isnull=True,
            expires_at__gt=now,
        ).order_by('-created_at').first()

        if verification is None:
            raise serializers.ValidationError('Verification code is invalid or expired')

        if verification.attempt_count >= 5:
            verification.used_at = now
            verification.save(update_fields=['used_at'])
            raise serializers.ValidationError('Too many failed attempts, please request a new code')

        if not check_password(code, verification.code_hash):
            verification.attempt_count += 1
            if verification.attempt_count >= 5:
                verification.used_at = now
                verification.save(update_fields=['attempt_count', 'used_at'])
            else:
                verification.save(update_fields=['attempt_count'])
            raise serializers.ValidationError('Verification code is invalid or expired')

        user = User.objects.filter(email=email).first()
        if user is None:
            raise serializers.ValidationError('User not found')

        attrs['email'] = email
        attrs['user'] = user
        attrs['verification'] = verification
        return attrs

    def create(self, validated_data):
        user = validated_data['user']
        user.password = make_password(validated_data['new_password'])
        user.save(update_fields=['password', 'updated_at'])

        verification = validated_data['verification']
        verification.used_at = timezone.now()
        verification.save(update_fields=['used_at'])

        return {'user_id': user.user_id}
