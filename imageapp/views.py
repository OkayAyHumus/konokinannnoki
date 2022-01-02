from django.shortcuts import render, redirect
from .forms import ImageForm, LoginForm, SignUpForm
from .models import ModelFile
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate





from torchvision import transforms
from PIL import Image

import torch
# import torch.nn as nn
import torch.nn.functional as F
import numpy as np

import sys
sys.path.append('../')
from model.mymodel import Net

transform = transforms.Compose([
                                transforms.ToTensor(),
                                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])


@login_required
def index(request):
    if request.method == 'POST':
        img = ModelFile.objects.all()
        # img = img[0]
        img_name = request.FILES['image']
        image_url = 'media/documents/{}'.format(img_name)
   

        form = ImageForm(request.POST, request.FILES)
       
        if form.is_valid():
            form.save()
            im = np.array(Image.open(image_url))
            im = transform(im)


            net =Net().cpu().eval()
            net.load_state_dict(torch.load('/model/f_omomi.pt', map_location=torch.device('cpu')))
            y = net(im.unsqueeze(0))
            y_proba = F.softmax(y, dim=-1)
            y_proba = y.sort(dim=1, descending=True)
            y_proba_p = round(y_proba[0][0][0].item(),1)*10
            y_result = torch.argmax(y)
            if y_result==0:
                y_result_t ='銀杏'
            elif y_result==1:
                y_result_t ='紅葉'
            else:
                y_result_t ='桜'

            ModelFile.objects.create(label=y_result_t, proba=y_proba_p)
            
            return render(request,'imageapp/classify.html',{'y_result':y_result,'y_proba_p':y_proba_p , 'image_url':image_url})

    else:
        form = ImageForm()
        return render(request, 'imageapp/index.html', {'form':form})



class Login(LoginView):
    form_class=LoginForm
    template_name='imageapp/login.html'


class Logout(LogoutView):
    template_name = 'imageapp/base.html'

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')

            new_user = authenticate(username=username, password=password)

            if new_user is not None:
                login(request, new_user)
                return redirect('index')
            else:
                form = SignUpForm(request.POST)
                return render(request, 'imageapp/signup.html', {'form':form})
        else:
             form = SignUpForm(request.POST)
             render(request, 'imageapp/signup.html', {'form':form})
    else:
        form = SignUpForm()
        return render(request, 'imageapp/signup.html', {'form':form})

