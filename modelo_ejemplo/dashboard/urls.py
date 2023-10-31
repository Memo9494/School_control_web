from django.urls import path
from .views import HomeView, CourseDetailView,video_feed


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('<int:pk>/take_attendance', video_feed, name='take_attendance'),
]