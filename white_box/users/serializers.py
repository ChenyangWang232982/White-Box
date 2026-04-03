from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import User


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
