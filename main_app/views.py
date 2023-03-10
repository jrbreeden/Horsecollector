from django.shortcuts import render, redirect
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic import ListView, DetailView
from .models import Horse, Toy, Photo
from .forms import FeedingForm
import uuid
import boto3
import os
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse
from main_app.serializer import MyTokenObtainPairSerializer, RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from . models import *
from . serializer import *




# Create your views here.
class ReactView(APIView):
    
    serializer_class = ReactSerializer
  
    def get(self, request):
        detail = [ {"name": detail.name,"detail": detail.detail} 
        for detail in React.objects.all()]
        return Response(detail)
  
    def post(self, request):
  
        serializer = ReactSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return  Response(serializer.data)





class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


@api_view(['GET'])
def getRoutes(request):
    routes = [
        '/api/token/',
        '/api/register/',
        '/api/token/refresh/'
    ]
    return Response(routes)

def home(request):
  return render(request, 'home.html')

def about(request):
  return render(request, 'about.html')

@login_required
def horses_index(request):
  horses = Horse.objects.filter(user=request.user)
  return render(request, 'horses/index.html', { 'horses': horses })

@login_required
def horses_detail(request, horse_id):
  horse = Horse.objects.get(id=horse_id)
  # Get the toys the horse doesn't have...
  # First, create a list of the toy ids that the horse DOES have
  id_list = horse.toys.all().values_list('id')
  # Now we can query for toys whose ids are not in the list using exclude
  toys_horse_doesnt_have = Toy.objects.exclude(id__in=id_list)
  # instantiate FeedingForm to be rendered in the detail.html template
  feeding_form = FeedingForm()
  return render(request, 'horses/detail.html', { 
    'horse': horse, 
    'feeding_form': feeding_form, 
    'toys': toys_horse_doesnt_have
    })


class HorseCreate(LoginRequiredMixin, CreateView):
  model = Horse
  fields = ['name', 'breed', 'description', 'age']

  # This inherited method is called when a
  # valid cat form is being submitted
  def form_valid(self, form):
    # Assign the logged in user (self.request.user)
    form.instance.user = self.request.user  # form.instance is the horse
    # Let the CreateView do its job as usual
    return super().form_valid(form)

class HorseUpdate(LoginRequiredMixin, UpdateView):
  model = Horse
  fields = ['breed', 'description', 'age']

class HorseDelete(LoginRequiredMixin, DeleteView):
  model = Horse
  success_url = '/horses/'

@login_required
def add_feeding(request, horse_id):
  # create a ModelForm instance using the data in the posted form
  form = FeedingForm(request.POST)
  # validate the data
  if form.is_valid():
    new_feeding = form.save(commit=False)
    new_feeding.horse_id = horse_id
    new_feeding.save()
  return redirect('detail', horse_id=horse_id)

class ToyList(LoginRequiredMixin, ListView):
  model = Toy

class ToyDetail(LoginRequiredMixin, DetailView):
  model = Toy

class ToyCreate(LoginRequiredMixin, CreateView):
  model = Toy
  fields = '__all__'

class ToyUpdate(LoginRequiredMixin, UpdateView):
  model = Toy
  fields = ['name', 'color']

class ToyDelete(LoginRequiredMixin, DeleteView):
  model = Toy
  success_url = '/toys/'

@login_required
def assoc_toy(request, horse_id, toy_id):
  Horse.objects.get(id=horse_id).toys.add(toy_id)
  return redirect('detail', horse_id=horse_id)

@login_required
def add_photo(request, horse_id):
  # photo-file will be the "name" attribute on the <input type="file">
  photo_file = request.FILES.get('photo-file', None)
  if photo_file:
      s3 = boto3.client('s3')
      # need a unique "key" for S3 / needs image file extension too
      key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]
      # just in case something goes wrong
      try:
        bucket = os.environ['S3_BUCKET']
        s3.upload_fileobj(photo_file, bucket, key)
        # build the full url string
        url = f"{os.environ['S3_BASE_URL']}{bucket}/{key}"
        # we can assign to horse_id or horse (if you have a horse object)
        Photo.objects.create(url=url, horse_id=horse_id)
      except Exception as e:
        print('An error occurred uploading file to S3')
        print(e)
  return redirect('detail', horse_id=horse_id)

def signup(request):
  error_message = ''
  if request.method == 'POST':
    form = UserCreationForm(request.POST)
    if form.is_valid():
      user = form.save()
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)