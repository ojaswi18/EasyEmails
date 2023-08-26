"""EasyEmails URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from django.urls import path , include
from django.contrib.auth import views as auth_views
from MainApp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
    path('sortedemails/<str:slug>',views.sortedemails,name="sortedemails"),  
    path('googlecalendar/',views.googlecalendar,name="googlecalendar"),
    path('compose/',views.compose,name="compose"),
    path('sendEmail/',views.sendEmail,name="sendEmail"),
    path('addevent/',views.addevent,name="addevent"), 
    path('create_event/',views.create_event,name="create_event"),
    path('emailbody/',views.emailbody,name="emailbody"),
    path('starEmail/<str:email_id>/', views.starEmail, name='starEmail'),
    path('deleteEmail/<str:email_id>/', views.delete_email, name='delete_email'),
    path('forward/<str:email_id>/', views.forward, name='forward'),
    path('reply/<str:email_id>/', views.reply, name='reply'),
    # path('server_start_time/', views.server_start_time, name='server_start_time'),
    path('getProcessedEmails/', views.get_processed_emails, name='get_processed_emails'),

]
