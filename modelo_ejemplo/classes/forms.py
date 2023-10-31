from django import forms
from django.forms import ModelForm, BaseModelForm
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, Attendance, Participation, Course

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = CustomUser
        fields = {'username','first_name','last_name','email','age','degree','semester','photo'}

    
class CustomUserChangeForm(ModelForm):
    class Meta(UserChangeForm):
        model = CustomUser
        fields = {'username','first_name','last_name','email','age','degree','semester','courses','is_staff','is_superuser','photo','face_encoding'}
        widgets = {'courses': forms.CheckboxSelectMultiple(),'photo': forms.FileInput()}

# class CustomCourseCreationForm(ModelForm):
#     class Meta:
#         model = Course
#         fields = {'name'}


# class CustomCourseChangeForm(BaseModelForm):
#     class Meta:
#         model = Course
#         fields = {'name'}

# class CustomAttendanceCreationForm(forms.Form):
#     class Meta:
#         model = Attendance
#         fields = {'user','course','date','is_attended'}

# class CustomAttendanceChangeForm(forms.Form):
#     class Meta:
#         model = Attendance
#         fields = {'user','course','date','is_attended'}

# class CustomParticipationCreationForm(forms.Form):
#     class Meta:
#         model = Participation
#         fields = {'user','course','date','is_participated'}

# class CustomParticipationChangeForm(forms.Form):
#     class Meta:
#         model = Participation
#         fields = {'user','course','date','is_participated'}

