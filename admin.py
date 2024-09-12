from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Hotels, Sejur, Renter, Landlord

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'name', 'role', 'is_staff', 'is_active') 
    list_filter = ('is_staff', 'is_active', 'role')
    
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password', 'name')}),  
        ('Personal info', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_permissions', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'role', 'password1', 'password2'),  
        }),
    )
    
    search_fields = ('username', 'email', 'name') 
    ordering = ('username',)

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Hotels)
admin.site.register(Sejur)
admin.site.register(Renter)
admin.site.register(Landlord)
