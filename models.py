from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    RENTER = 'renter'
    LANDLORD = 'landlord'

    ROLE_CHOICES = [
        (RENTER, 'Renter'),
        (LANDLORD, 'Landlord'),
    ]
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, null=True, blank=True) 
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=RENTER)
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username
    

class Renter(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='renter')
    name = models.CharField(max_length=100, default="")
    preferences = models.JSONField(null=True, blank=True)  
    centroid_latitude = models.FloatField(null=True, blank=True)  
    centroid_longitude = models.FloatField(null=True, blank=True)  
    rented_hotels = models.JSONField(null=True, blank=True) 

    def __str__(self):
        return f"{self.user.username} (Renter)"

    def update_preference(self, preference):
        """Actualizează frecvența unei preferințe specifice"""
        if not self.preferences:
            self.preferences = {}
        
        if preference in self.preferences:
            self.preferences[preference] += 1
        else:
            self.preferences[preference] = 1
        
        self.save()

    def update_location(self, latitude, longitude):
        """Actualizează centroidul geografic """
        if self.centroid_latitude is None or self.centroid_longitude is None:
            self.centroid_latitude = latitude
            self.centroid_longitude = longitude
        else:
            # Because the area was Romania, the centroid is calculated with the avg. function, not the Cartesian Coord function
            n = len(self.rented_hotels) if self.rented_hotels else 1
            self.centroid_latitude = (self.centroid_latitude * n + latitude) / (n + 1)
            self.centroid_longitude = (self.centroid_longitude * n + longitude) / (n + 1)
        
        self.save()


class Landlord(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='landlord')
    name = models.CharField(max_length=100, default="")
    email = models.EmailField(unique=True)
    listed_hotels = models.JSONField(null=True, blank=True) 

    def __str__(self):
        return f"{self.user.username} (Landlord)"

import uuid

class Hotels(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)  # Utilizează UUIDField
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    amenities = models.JSONField()
    phone = models.CharField(max_length=20)
    review_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    latitude = models.FloatField()
    longitude = models.FloatField()
    money = models.FloatField(default=0.0)
    
    def __str__(self):
        return self.name

    class Meta:
        db_table = 'hotels'

class Sejur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    renter = models.ForeignKey(Renter, on_delete=models.CASCADE)  
    hotel = models.ForeignKey(Hotels, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_people = models.IntegerField()
    money = models.FloatField(default=0.0)
    rating = models.FloatField(null=True, blank=True)
    feedback = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Sejur at {self.hotel.name}'

    class Meta:
        db_table = 'sejur'


