from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import DatabaseError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from datetime import date

from .models import CustomUser, Hotels, Sejur, Renter, Landlord
from .forms import SejurForm


from .recommendations import (
    combined_recommendations,
)


# View pentru înregistrare
def signup_view(request):
    if request.method == "POST":
        username = request.POST['user_name']
        email = request.POST['email']
        name = request.POST['name']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        role = request.POST['role']
        
        # Verifică dacă username-ul există deja
        if CustomUser.objects.filter(username=username).exists():
            #messages.error(request, "Acest username există deja!")
            return redirect('home-view')
        
        # Verifică dacă email-ul există deja
        if CustomUser.objects.filter(email=email).exists():
            #messages.error(request, "mail existent")
            return redirect('home-view')
        
        # Verifică lungimea username-ului
        if len(username) > 20:
            #messages.error(request, "Username-ul trebuie să aibă max char20")
            return redirect('home-view')
        
        # Verifică dacă parolele se potrivesc
        if password1 != password2:
            #messages.error(request, "Ati introdus doua parole diferite!")
            return redirect('home-view')
        
        # Verifică dacă username-ul este alfanumeric
        if not username.isalnum():
            #messages.error(request, "Username-ul trebuie să fie valid!")
            return redirect('home-view')
        
        # Crearea utilizatorului
        myuser = CustomUser.objects.create_user(username=username, email=email, password=password1)
        myuser.name = name
        myuser.role = role
        myuser.is_active = True
        myuser.save()

        # Asocierea cu `Renter` sau `Landlord`
        if myuser.role == CustomUser.RENTER:
            Renter.objects.create(user=myuser, name=myuser.name)
        elif myuser.role == CustomUser.LANDLORD:
            Landlord.objects.create(user=myuser, name=myuser.name, email=myuser.email)
        
        #messages.success(request, "Contul dvs. a fost creat cu succes! Vă rugăm să vă autentificați.")
        return redirect('home-view')

    return render(request, 'index.html')



# View pentru autentificare
def login_view(request):
    if request.method == "POST":
        try:
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                username = form.cleaned_data.get('username')
                password = form.cleaned_data.get('password')
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    #messages.success(request, "V-ați autentificat cu succes!")
                    return redirect('profile-view')
                else:
                    #messages.error(request, "Username sau parolă invalide!")
                    return redirect('login-view')
            else:
                #messages.error(request, "Formularul de autentificare nu este valid.")
                return redirect('login-view')
        except DatabaseError as e:
            #messages.error(request, f"Eroare de bază de date: {e}")
            print(f"Database error during login: {type(e).__name__} - {e}")
            return redirect('login-view')
    else:
        form = AuthenticationForm()
    return render(request, 'index.html', {'form': form})


# View pentru deconectare
def logout_view(request):
    try:
        logout(request)
        return redirect('home-view')
    except Exception as e:
        print(f"Error during logout: {e}")
        return redirect('home-view')

# Alte vizualizări
def home_view(request):
    if request.user.is_authenticated:
        if request.user.role == 'renter':
            return redirect('profile-view')
        elif request.user.role == 'landlord':
            return redirect('landlord-view')
    return render(request, 'index.html')


@login_required
def newhotel_view(request):

    if not hasattr(request.user, 'landlord'):
        return redirect('profile-view')  # Redirecționează utilizatorii neautorizați către profilul lor

    if request.method == 'POST':
        name = request.POST['name']
        address = request.POST['address']
        location = request.POST['location']
        amenities = request.POST['amenities']
        phone = request.POST['phone']
        money = request.POST['money']
        latitude = request.POST['latitude']
        longitude = request.POST['longitude']

        # Creează un nou hotel
        hotel = Hotels.objects.create(
            name=name,
            address=address,
            location=location,
            amenities=amenities.split(','),  # Presupunând că facilitățile sunt introduse ca listă de stringuri separate prin virgulă
            phone=phone,
            money=float(money),
            latitude=float(latitude),
            longitude=float(longitude)
        )

        # Adaugă hotelul în lista de hoteluri ale landlord-ului curent
        landlord = request.user.landlord
        if landlord.listed_hotels is None:
            landlord.listed_hotels = []
        landlord.listed_hotels.append(str(hotel.id))  # Adaugă ID-ul hotelului la lista hotelurilor
        landlord.save()

        return redirect('landlord-view')

    return render(request, 'newhotel.html')

@login_required
def hotels_view(request):
    if not hasattr(request.user, 'landlord'):
        return redirect('profile-view')  # Redirecționează utilizatorii neautorizați către profilul lor
    return render(request, 'hotels.html')

@login_required
def acasa_view(request):

    # if not hasattr(request.user, 'renter'):
    #     return redirect('landlord-view')  # Redirecționează utilizatorii care nu sunt renteri
    # # Obține hotelurile recomandate folosind funcția `combined_recommendations`
    recommended_hotels = combined_recommendations(request.user.id)

    if request.method == 'POST':
        mutable_post = request.POST.copy()
        hotel_ids = mutable_post.getlist('hotel')
        hotel_id = next((h for h in hotel_ids if h), None)
        
        if hotel_id:
            mutable_post.setlist('hotel', [hotel_id])
        else:
            form = SejurForm(request.POST)
            form.add_error('hotel', 'Hotelul nu este selectat corect.')
            return render(request, 'acasa.html', {'hotels': recommended_hotels, 'form': form})
        
        form = SejurForm(mutable_post)
        
        if form.is_valid():
            sejur = form.save(commit=False)
            sejur.renter = request.user.renter
            sejur.hotel_id = hotel_id
            sejur.save()

            # Update Renter's rented hotels list
            renter = request.user.renter
            hotel = Hotels.objects.get(id=hotel_id)

            if renter.rented_hotels is None:
                renter.rented_hotels = []
            
            if hotel.name not in renter.rented_hotels:
                renter.rented_hotels.append(hotel.name)
                renter.save()

            # Actualizează locația pentru Renter
            renter.update_location(hotel.latitude, hotel.longitude)  # Actualizează centroidul utilizatorului

            # Ensure amenities is a list before processing
            amenities = hotel.amenities if isinstance(hotel.amenities, list) else hotel.amenities.split(',')

            # Update preferences based on selected hotel amenities
            for amenity in amenities:
                renter.update_preference(amenity.strip())
            
            return redirect('profile-view')
        else:
            print("Form errors:", form.errors)

    else:
        form = SejurForm()

    # Asigură-te că hotelurile sunt transmise corect către template
    return render(request, 'acasa.html', {'hotels': recommended_hotels, 'form': form})



@login_required
@require_POST
def submit_review(request, stay_id):

    if not hasattr(request.user, 'renter'):
        return redirect('landlord-view')  # Redirecționează utilizatorii care nu sunt renteri
    stay = get_object_or_404(Sejur, id=stay_id, renter=request.user.renter)

    rating = int(request.POST.get('rating', 0))
    if 1 <= rating <= 5:
        stay.rating = rating
        stay.save()

        # Actualizarea ratingului mediu al hotelului
        hotel = stay.hotel
        
        # Calculul ratingului mediu ponderat
        k = 5  # Factor de ajustare, poate fi modificat în funcție de nevoi
        
        total_reviews = hotel.review_count
        initial_total = hotel.average_rating * total_reviews
        new_total = initial_total + rating
        total_reviews += 1
        
        # Calculează media ponderată
        hotel.average_rating = (initial_total + k * rating) / (total_reviews + k)
        hotel.review_count = total_reviews
        hotel.save()

        #messages.success(request, 'Recenzia ta a fost trimisă cu succes și nota hotelului a fost actualizată!')
    else:
        #messages.error(request, 'Recenzia ta nu a fost validă.')
        return redirect('profile-view')

    return redirect('profile-view')

@login_required
def profile_view(request):

    if not hasattr(request.user, 'renter'):
        return redirect('landlord-view')  # Redirecționează utilizatorii care nu sunt renteri
    user = request.user
    
    # Verifică dacă utilizatorul are rolul de 'renter'
    if user.role != CustomUser.RENTER:
        return redirect('home-view')  # Redirecționează la pagina de home dacă nu este renter

    current_date = date.today()

    # Obține șederile anterioare și viitoare
    past_stays = Sejur.objects.filter(renter=user.renter, end_date__lt=current_date) | Sejur.objects.filter(renter=user.renter, start_date__lt=current_date, end_date__gte=current_date)
    future_stays = Sejur.objects.filter(renter=user.renter, start_date__gte=current_date)

    context = {
        'user': user,
        'past_stays': past_stays,
        'future_stays': future_stays,
    }

    return render(request, 'profile.html', context)

@login_required
def landlord_view(request):

    if not hasattr(request.user, 'landlord'):
        return redirect('profile-view')  # Redirecționează utilizatorii neautorizați către profilul lor
    
    # Obține obiectul Landlord asociat utilizatorului curent
    landlord = request.user.landlord

    # Extrage ID-urile hotelurilor listate de landlord
    hotel_ids = landlord.listed_hotels or []

    # Preia hotelurile din baza de date folosind aceste ID-uri
    hotels = Hotels.objects.filter(id__in=hotel_ids)

    context = {
        'user': request.user,
        'hotels': hotels,  # Trimite lista hotelurilor către template
    }

    return render(request, 'landlord.html', context)

@login_required
def edit_hotel_view(request, hotel_id):

    if not hasattr(request.user, 'landlord'):
        return redirect('profile-view')  # Redirecționează utilizatorii neautorizați către profilul lor
    hotel = get_object_or_404(Hotels, id=hotel_id)

    if request.method == 'POST':
        hotel.name = request.POST['name']
        hotel.address = request.POST['address']
        hotel.location = request.POST['location']
        hotel.amenities = request.POST['amenities'].split(',')
        hotel.phone = request.POST['phone']
        hotel.money = float(request.POST['money'])
        hotel.latitude = float(request.POST.get('latitude', hotel.latitude))  # Folosește valoarea existentă dacă nu este în POST
        hotel.longitude = float(request.POST.get('longitude', hotel.longitude))  # Folosește valoarea existentă dacă nu este în POST
        hotel.save()

        return redirect('landlord-view')

    context = {
        'hotel': hotel,
    }
    return render(request, 'newhotel.html', context)
