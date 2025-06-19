"""
URL configuration for CHAOS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chaos_core.urls')),
    path('information/', include('chaos_information.urls')),
    path('chat/', include('chaos_chat.urls')),
    path('assistent/' , include('chaos_assistent.urls')),
    path('organizer/' , include('chaos_organizer.urls')),
    path('documents/', include('chaos_documents.urls')),
    path('mentor/', include('chaos_mentor.urls')),
    path('journal/', include('chaos_journal.urls')),
]
