import math
import unicodedata
import pandas as pd
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .models import CustomUser, Hotels, Sejur

# Listă de stop words pentru limba română
romanian_stop_words = [
    'în', 'si', 'și', 'de', 'la', 'pe', 'cu', 'pentru', 'din', 'sa', 'să', 
    'a', 'este', 'fost', 'care', 'fi', 'că', 'ca', 'o', 'nu', 'un', 'lui', 
    'acest', 'acesta', 'al', 'sau', 'ea', 'între', 'intre', 'nici', 'mai', 
    'decât', 'doar', 'decât', 'fără', 'fara'
]

def remove_diacritics(text):
    """Elimină diacriticele dintr-un text."""
    normalized_text = unicodedata.normalize('NFD', text)
    return ''.join([c for c in normalized_text if unicodedata.category(c) != 'Mn'])

def preferences_to_string(preferences):
    """Transformă dicționarul de preferințe într-un string."""
    if isinstance(preferences, dict):
        return ' '.join([f"{key} " * value for key, value in preferences.items()])
    return str(preferences)


def get_recommendations(user_id):
    """Oferă recomandări bazate pe cuvinte cheie pentru un utilizator specific."""
    user = CustomUser.objects.get(pk=user_id)

    combined_string = "" #initializarea variabilei
    if hasattr(user, 'renter') and user.renter.preferences:
        user_preferences = preferences_to_string(user.renter.preferences)
        

        user_locations = ""  
        
        combined_string = f"{user_preferences} {user_locations}"  # Combina pref
        return Hotels.objects.none()
    
    hotels = Hotels.objects.all()

    #crearea unui dataframe
    hotel_data = [{
        'hotel_id': hotel.id,
        'description': remove_diacritics(f"{preferences_to_string(hotel.amenities)} {hotel.location}")
    } for hotel in hotels]
    df = pd.DataFrame(hotel_data)

    tfidf = TfidfVectorizer(stop_words=romanian_stop_words) #term freq - inv doc freq
    tfidf_matrix = tfidf.fit_transform(df['description'])

    user_pref_vector = tfidf.transform([remove_diacritics(combined_string)]) #vectorizarea

    #calc similitudinea cos a vectorilor
    cosine_sim = linear_kernel(user_pref_vector, tfidf_matrix)

    sim_scores = list(enumerate(cosine_sim[0]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    top_hotels = [df.iloc[i[0]].hotel_id for i in sim_scores]

    recommended_hotels = Hotels.objects.filter(id__in=top_hotels)
    
    return recommended_hotels




def get_rating_based_recommendations(user_id, min_reviews=5):
    """Recomandă hoteluri bazate pe rating-urile medii ponderate și pe rating-urile date de utilizator."""
    user = CustomUser.objects.get(pk=user_id)
    
    # Obtine toate sejururile 
    user_stays = Sejur.objects.filter(renter=user.renter)

    # Creeaza un dict cu scorurile date de utilizator pentru fiecare hotel
    user_ratings = {stay.hotel.id: stay.rating for stay in user_stays if stay.rating is not None}

    hotels = Hotels.objects.all()

    # Parametrii pentru media Bayesiana
    k = 10  # Factor de ponderare (poate fi ajustta)
    C = np.mean([hotel.average_rating for hotel in hotels if hotel.review_count > 0])  # Media rating-urilor
    hotel_ratings = {}
    
    for hotel in hotels:
        if hotel.review_count > 0:
            weighted_rating = (hotel.review_count / (hotel.review_count + k)) * hotel.average_rating + (k / (hotel.review_count + k)) * C
        else:
            weighted_rating = hotel.average_rating  # Rating-ul brut pentru hoteluri fără recenzii
            
        # Ajustează ratingul folosind personalized rating
        if hotel.id in user_ratings:
            personal_rating = user_ratings[hotel.id]
            combined_rating = 0.7 * personal_rating + 0.3 * weighted_rating
        else:
            combined_rating = weighted_rating
        
        hotel_ratings[hotel.id] = combined_rating

    # Sortează hotelurile dupa combined rating
    top_rated_hotels = sorted(hotel_ratings.items(), key=lambda x: x[1], reverse=True)
    top_hotels_ids = [hotel_id for hotel_id, rating in top_rated_hotels]
    # Return dupa combined score
    recommended_hotels = Hotels.objects.filter(id__in=top_hotels_ids)
    return recommended_hotels













def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculează distanța Euclidiană între două puncte geografice."""
    return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)


def recommend_hotels_based_on_geolocation(renter):
    """Recomandă hoteluri bazate pe proximitatea față de centroidul geografic al utilizatorului."""
    if renter.centroid_latitude is None or renter.centroid_longitude is None:
        return Hotels.objects.none()

    hotels = Hotels.objects.all()
    distances = []

    for hotel in hotels:
        distance = calculate_distance(renter.centroid_latitude, renter.centroid_longitude, hotel.latitude, hotel.longitude)
        distances.append((hotel, distance))

    distances.sort(key=lambda x: x[1])  # Sortează hotelurile după distanță

    recommended_hotels = [hotel for hotel, _ in distances]
    
    return recommended_hotels


def normalize_scores(scores):
    """Normalizează o listă de scoruri între 0 și 1."""
    if not scores:
        return [0] * len(scores)
    
    min_score = min(scores)
    max_score = max(scores)
    
    if min_score == max_score:
        return [1] * len(scores)
    
    return [(score - min_score) / (max_score - min_score) for score in scores]


from django.db.models import Case, When, Value, IntegerField

def combined_recommendations(user_id, weights=(0.4, 0.3, 0.3), min_user_rating=3):
    # Identifica Renter-ul dupa user_id
    renter = CustomUser.objects.get(pk=user_id).renter

    # Filtreaza sejururile bazate pe renter_id
    user_stays = Sejur.objects.filter(renter_id=renter.id)

    # Get all user ratings dynamically
    rated_hotels = {stay.hotel.id: stay.rating for stay in user_stays if stay.rating is not None}

    # Apply default rating if hotel is not rated
    all_hotel_ids = Hotels.objects.values_list('id', flat=True)
    for hotel_id in all_hotel_ids:
        if hotel_id not in rated_hotels:
            rated_hotels[hotel_id] = 4  # Default to 4 if not rated

    cbf_hotels = get_recommendations(user_id)
    rating_hotels = get_rating_based_recommendations(user_id)
    geo_hotels = recommend_hotels_based_on_geolocation(renter)

    cbf_weight, rating_weight, geo_weight = weights
    cbf_scores = {hotel.id: index for index, hotel in enumerate(cbf_hotels)} if cbf_hotels else {}
    cbf_norm = normalize_scores(list(cbf_scores.values())) if cbf_scores else []
    rating_scores = {hotel.id: index for index, hotel in enumerate(rating_hotels)} if rating_hotels else {}
    rating_norm = normalize_scores(list(rating_scores.values())) if rating_scores else []
    geo_scores = {hotel.id: index for index, hotel in enumerate(geo_hotels)} if geo_hotels else {}
    geo_norm = normalize_scores(list(geo_scores.values())) if geo_scores else []
    combined_scores = {}

    for hotel in Hotels.objects.filter(id__in=set(cbf_scores.keys()) | set(rating_scores.keys()) | set(geo_scores.keys())):
        cbf_score = cbf_norm[cbf_scores[hotel.id]] if hotel.id in cbf_scores else 0
        rating_score = rating_norm[rating_scores[hotel.id]] if hotel.id in rating_scores else 0
        geo_score = geo_norm[geo_scores[hotel.id]] if hotel.id in geo_scores else 0
        combined_score = (cbf_weight * cbf_score) + (rating_weight * rating_score) + (geo_weight * geo_score)

        # Fetch the most recent rating for the hotel
        rating = rated_hotels.get(hotel.id, 4)  # Default to 4 if no explicit rating
        # Apply the actual rating influence
        if rating == 4:
            pass  # Do nothing for rating 4
        elif rating < 4:  # Apply penalties for ratings below 4
            if rating == 3:
                combined_score *= 0.7  
            elif rating == 2:
                combined_score *= 0.5  
            elif rating == 1:
                combined_score *= 0.3  
        elif rating == 5:
            combined_score *= 20  
        combined_scores[hotel.id] = combined_score

    # Sorting based on the combined score
    sorted_hotels = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
    top_hotels_ids = [hotel_id for hotel_id, score in sorted_hotels]

    # Creating a Case for ordering - based on the calculated scores
    ordering = Case(
        *[When(id=hotel_id, then=pos) for pos, hotel_id in enumerate(top_hotels_ids)],
        output_field=IntegerField()
    )

    # Return the ordered hotels
    recommended_hotels = Hotels.objects.filter(id__in=top_hotels_ids).order_by(ordering)

    return recommended_hotels