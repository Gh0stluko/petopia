from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes, api_view, action
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Product, Image, Animal_Category,Item_Category, Cart, Order, OrderItem
from rest_framework import viewsets
from .serializer import CustomUserSerializer, ProductSerializer, ImageSerializer, AnimalSerializer,ItemSerialiazer, CartSerializer, ProductRatingSerializer, OrderSerializer, OrderDetailSerializer
from .models import Product, ProductRating
from django.views.decorators.csrf import csrf_exempt  # Added import
from django.utils.decorators import method_decorator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profile_complete(request):
    try:

        user = request.user
        username = request.data.get('username')
        password = request.data.get('password')
        gender = request.data.get('gender')
        dateOfBirth = request.data.get('dateOfBirth')
        firstName = request.data.get('firstName')
        lastName = request.data.get('lastName')
        avatar = request.FILES.get('avatar')
        print(avatar)
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response(
                {'error': 'Username already taken'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        user.username = username
        user.set_password(password)
        user.gender = gender
        if dateOfBirth:

            user.date_birth = dateOfBirth
        user.first_name = firstName
        user.last_name = lastName

        user.avatar = avatar  # Directly assign the file

        user.registration_complete = True
        user.save()
        
        return Response({'message': 'Profile completed successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred while completing profile'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def LoginView(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response(
            {'error': 'Please provide both email and password.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    refresh = RefreshToken.for_user(user)
    
    # Create response with access token
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'username': user.username,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def RegisterView(request):
    if request.method == 'POST':
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = CustomUser(username=username, email=email)
        user.set_password(password)
        user.date_joined = timezone.now()
        user.save()

        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:

        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not user.check_password(old_password):
            print("old password is incorrect")
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'An error occurred while changing password'}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    try:
        user = request.user
        user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'An error occurred while deleting account'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({'error': 'No refresh token provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        response = Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response
    except Exception as e:
        return Response({'error': 'An error occurred during logout.'}, status=status.HTTP_400_BAD_REQUEST)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, methods=['put'], url_path='update_avatar')
    def update_avatar(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['get'], url_path='get_reviews')
    def get_reviews(self, request):
        user = request.user
        product_id = request.query_params.get('product_id')
        
        if product_id:
            reviews = ProductRating.objects.filter(user=user, product_id=product_id)
        else:
            reviews = ProductRating.objects.filter(user=user)
        
        serializer = ProductRatingSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['put'], url_path='update_wishlist')
    def update_wishlist(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        if product in user.wishlist.all():
            print("removed")
            user.wishlist.remove(product)
            user.save()
            return Response({'message': 'Product removed from wishlist'}, status=status.HTTP_200_OK)
        else:
            user.wishlist.add(product)
            user.save()
            print("added")
            return Response({'message': 'Wishlist updated successfully'}, status=status.HTTP_200_OK)
            
        return Response({'message': 'Wishlist updated successfully'}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retrieve the current authenticated user's data.
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Update the current authenticated user's data."""
        user = request.user
        data = request.data

        serializer = self.get_serializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print("error", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Q, Max
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.prefetch_related('ratings')
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        product = self.get_object()
        rating = request.data.get('rating')
        print(rating)
        print(request.user)

        if not rating or not (1 <= int(rating) <= 5):
            return Response({"error": "Rating must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        ProductRating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating}
        )

        return Response({"average_rating": product.average_rating}, status=status.HTTP_200_OK)
    def get_queryset(self):
        queryset = Product.objects.prefetch_related('ratings')

        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Animal category filter
        animal_categories = self.request.query_params.getlist('animal_category')
        print(animal_categories)
        if animal_categories:
            queryset = queryset.filter(Animal_Category__name__in=animal_categories)

        # Item category filter
        item_categories = self.request.query_params.getlist('item_category')
        print(item_categories)
        if item_categories:
            queryset = queryset.filter(Item_Category__name__in=item_categories)

        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        sort_by = self.request.query_params.get('sort_by')
        if sort_by:
            if sort_by == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_desc':
                queryset = queryset.order_by('-price')
            elif sort_by == 'newest':
                queryset = queryset.order_by('-created_at')

        return queryset.distinct()
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def max_price(self, request):
        max_price = Product.objects.aggregate(Max('price'))['price__max']
        return Response({'max_price': max_price})
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

@permission_classes([AllowAny])
class AnimalCategoryViewSet(viewsets.ModelViewSet):
    queryset =  Animal_Category.objects.all()
    serializer_class = AnimalSerializer


@permission_classes([AllowAny])
class ItemCategoryViewSet(viewsets.ModelViewSet):
    queryset =  Item_Category.objects.all()
    serializer_class = ItemSerialiazer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

User = get_user_model()



@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    access_token = request.data.get('google_token')
    try:
        # Specify the CLIENT_ID of your app that you get from the Google Developer Console
        idinfo = id_token.verify_oauth2_token(access_token, requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID)
        print("Google token info:", idinfo)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', '')
        # Check if the user exists
        email_prefix = email.split('@')[0]
        user, created = User.objects.get_or_create(email=email)
        
        if created:
            user.first_name = name.split()[0] if name else ''
            user.last_name = name.split()[-1] if name else ''
            user.date_joined = timezone.now()
            user.save()

        # Here you would typically create a session or return a token
        # For this example, we'll just return some user info

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'name': user.username,
            'access': access_token,
            'refresh': refresh_token,
        })

    except ValueError:
        # Invalid token
        return JsonResponse({'error': 'Invalid token'}, status=400)

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes, api_view, action
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, Product, Image, Animal_Category,Item_Category, Cart, Order, OrderItem
from rest_framework import viewsets
from .serializer import CustomUserSerializer, ProductSerializer, ImageSerializer, AnimalSerializer,ItemSerialiazer, CartSerializer, ProductRatingSerializer
from .models import Product, ProductRating
from django.views.decorators.csrf import csrf_exempt  # Added import
from django.utils.decorators import method_decorator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profile_complete(request):
    try:

        user = request.user
        username = request.data.get('username')
        password = request.data.get('password')
        gender = request.data.get('gender')
        dateOfBirth = request.data.get('dateOfBirth')
        firstName = request.data.get('firstName')
        lastName = request.data.get('lastName')
        avatar = request.FILES.get('avatar')
        print(avatar)
        if User.objects.filter(username=username).exclude(id=user.id).exists():
            return Response(
                {'error': 'Username already taken'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        user.username = username
        user.set_password(password)
        user.gender = gender
        if dateOfBirth:

            user.date_birth = dateOfBirth
        user.first_name = firstName
        user.last_name = lastName

        user.avatar = avatar  # Directly assign the file

        user.registration_complete = True
        user.save()
        
        return Response({'message': 'Profile completed successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({'error': 'An error occurred while completing profile'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def LoginView(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if email is None or password is None:
        return Response(
            {'error': 'Please provide both email and password.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    user = authenticate(request, email=email, password=password)

    if user is None:
        return Response(
            {'error': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    refresh = RefreshToken.for_user(user)
    
    # Create response with access token
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'username': user.username,
    }, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([AllowAny])
def RegisterView(request):
    if request.method == 'POST':
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if CustomUser.objects.filter(email=email).exists():
            return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = CustomUser(username=username, email=email)
        user.set_password(password)
        user.date_joined = timezone.now()
        user.save()

        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    try:

        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        if not user.check_password(old_password):
            print("old password is incorrect")
            return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'An error occurred while changing password'}, status=status.HTTP_400_BAD_REQUEST)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_account(request):
    try:
        user = request.user
        user.delete()
        return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': 'An error occurred while deleting account'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    try:
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token is None:
            return Response({'error': 'No refresh token provided.'}, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        response = Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        response.delete_cookie('refresh_token')
        return response
    except Exception as e:
        return Response({'error': 'An error occurred during logout.'}, status=status.HTTP_400_BAD_REQUEST)

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer

    @action(detail=False, methods=['put'], url_path='update_avatar')
    def update_avatar(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['get'], url_path='get_reviews')
    def get_reviews(self, request):
        user = request.user
        product_id = request.query_params.get('product_id')
        
        if product_id:
            reviews = ProductRating.objects.filter(user=user, product_id=product_id)
        else:
            reviews = ProductRating.objects.filter(user=user)
        
        serializer = ProductRatingSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=['put'], url_path='update_wishlist')
    def update_wishlist(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        if product in user.wishlist.all():
            print("removed")
            user.wishlist.remove(product)
            user.save()
            return Response({'message': 'Product removed from wishlist'}, status=status.HTTP_200_OK)
        else:
            user.wishlist.add(product)
            user.save()
            print("added")
            return Response({'message': 'Wishlist updated successfully'}, status=status.HTTP_200_OK)
            
        return Response({'message': 'Wishlist updated successfully'}, status=status.HTTP_200_OK)
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Retrieve the current authenticated user's data.
        """
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put'], permission_classes=[IsAuthenticated])
    def update_me(self, request):
        """Update the current authenticated user's data."""
        user = request.user
        data = request.data

        serializer = self.get_serializer(user, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            print("error", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.db.models import Q, Max
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.prefetch_related('ratings')
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        product = self.get_object()
        rating = request.data.get('rating')
        print(rating)
        print(request.user)

        if not rating or not (1 <= int(rating) <= 5):
            return Response({"error": "Rating must be between 1 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        ProductRating.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating}
        )

        return Response({"average_rating": product.average_rating}, status=status.HTTP_200_OK)
    def get_queryset(self):
        queryset = Product.objects.prefetch_related('ratings')

        # Search query
        search = self.request.query_params.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )

        # Animal category filter
        animal_categories = self.request.query_params.getlist('animal_category')
        print(animal_categories)
        if animal_categories:
            queryset = queryset.filter(Animal_Category__name__in=animal_categories)

        # Item category filter
        item_categories = self.request.query_params.getlist('item_category')
        print(item_categories)
        if item_categories:
            queryset = queryset.filter(Item_Category__name__in=item_categories)

        # Price range filter
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Sorting
        sort_by = self.request.query_params.get('sort_by')
        if sort_by:
            if sort_by == 'price_asc':
                queryset = queryset.order_by('price')
            elif sort_by == 'price_desc':
                queryset = queryset.order_by('-price')
            elif sort_by == 'newest':
                queryset = queryset.order_by('-created_at')

        return queryset.distinct()
    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def max_price(self, request):
        max_price = Product.objects.aggregate(Max('price'))['price__max']
        return Response({'max_price': max_price})
class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

@permission_classes([AllowAny])
class AnimalCategoryViewSet(viewsets.ModelViewSet):
    queryset =  Animal_Category.objects.all()
    serializer_class = AnimalSerializer


@permission_classes([AllowAny])
class ItemCategoryViewSet(viewsets.ModelViewSet):
    queryset =  Item_Category.objects.all()
    serializer_class = ItemSerialiazer

class CartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from social_django.utils import load_strategy, load_backend
from social_core.exceptions import MissingBackend, AuthTokenError, AuthForbidden
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings

User = get_user_model()



@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    access_token = request.data.get('google_token')
    try:
        # Specify the CLIENT_ID of your app that you get from the Google Developer Console
        idinfo = id_token.verify_oauth2_token(access_token, requests.Request(), settings.GOOGLE_OAUTH2_CLIENT_ID)
        print("Google token info:", idinfo)
        
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        email = idinfo['email']
        name = idinfo.get('name', '')
        # Check if the user exists
        email_prefix = email.split('@')[0]
        user, created = User.objects.get_or_create(email=email)
        
        if created:
            user.first_name = name.split()[0] if name else ''
            user.last_name = name.split()[-1] if name else ''
            user.date_joined = timezone.now()
            user.save()

        # Here you would typically create a session or return a token
        # For this example, we'll just return some user info

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return JsonResponse({
            'id': user.id,
            'email': user.email,
            'name': user.username,
            'access': access_token,
            'refresh': refresh_token,
        })

    except ValueError:
        # Invalid token
        return JsonResponse({'error': 'Invalid token'}, status=400)

@api_view(['POST'])
@permission_classes([AllowAny])
def create_order(request):
    data = request.data
    
    # Reconstruct items array from form data
    items = []
    item_index = 0
    while True:
        product_id_key = f'items[{item_index}][product_id]'
        quantity_key = f'items[{item_index}][quantity]'
        price_key = f'items[{item_index}][price]'
        
        if product_id_key not in data:
            break
            
        items.append({
            'product_id': data.get(product_id_key),
            'quantity': data.get(quantity_key),
            'price': data.get(price_key)
        })
        item_index += 1
    
    print("Отримані дані замовлення:", data)
    print("Реконструйовані товари:", items)
    
    try:
        # Створюємо замовлення
        order = Order(
            user=request.user if request.user.is_authenticated else None,
            status='pending',
            total_amount=data.get('total_amount', 0),
            payment_method=data.get('payment_method', 'cash'),
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            shipping_city=data.get('shipping_city', ''),
            shipping_address=data.get('shipping_address', '')
        )
        
        # Логуємо об'єкт замовлення перед збереженням
        print(f"Об'єкт замовлення перед збереженням: {order.__dict__}")
        
        order.save()
        
        # Додаємо товари до замовлення
        for item_data in items:
            product_id = item_data.get('product_id')
            
            try:
                product = Product.objects.get(id=product_id)
                item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    quantity=item_data.get('quantity', 1),
                    price=item_data.get('price', 0)
                )
                print(f"Створено товар замовлення: {item}")
            except Product.DoesNotExist:
                print(f"Помилка: Продукт з id {product_id} не знайдено")
            except Exception as item_err:
                print(f"Помилка при створенні товару: {str(item_err)}")
        
        return Response({
            'id': order.id,
            'status': order.status,
            'message': 'Замовлення успішно створено!'
        }, status=status.HTTP_201_CREATED)
    
    except Exception as e:
        print(f"Помилка створення замовлення: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)