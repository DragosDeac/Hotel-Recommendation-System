from django.contrib import admin
from django.urls import path
from .views import (
    home_view, signup_view, login_view, profile_view, hotels_view,
    logout_view, edit_hotel_view, newhotel_view, landlord_view, acasa_view,
    submit_review
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home-view'),
    path('signup/', signup_view, name='signup-view'),
    path('login/', login_view, name='login-view'),
    path('profile/', profile_view, name='profile-view'),
    path('hotels/', hotels_view, name='hotels-view'),
    path('logout/', logout_view, name='logout-view'),
    path('acasa/', acasa_view, name='acasa-view'),
    path('submit_review/<uuid:stay_id>/', submit_review, name='submit_review'),
    path('landlord/', landlord_view, name='landlord-view'),
    path('newhotel/', newhotel_view, name='newhotel-view'),
    path('edit-hotel/<uuid:hotel_id>/', edit_hotel_view, name='edit-hotel-view'),
]
