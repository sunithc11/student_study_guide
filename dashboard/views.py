from django.shortcuts import render,redirect
from django.contrib import messages
from django.views import generic
from youtubesearchpython import VideosSearch # type: ignore
from .forms import *
from .models import *
import requests
import wikipedia
from wikipedia.exceptions import DisambiguationError
from django.contrib.auth.decorators import login_required

# Create your views here.
def home(request):
    return render(request,'dashboard/home.html')


@login_required
def notes(request):
    if request.method =='POST':
        form = NotesForm(request.POST)
        if form.is_valid():
            notes = Notes(user=request.user,title=request.POST['title'],description=request.POST['description'])
            notes.save()
        # messages.success(request,f'Notes Added from {request.user.username} Successfully')
    else:
        form = NotesForm()
    notes = Notes.objects.filter(user=request.user)
    return render(request,'dashboard/notes.html',{'notes':notes,'form':form})

@login_required
def delete_note(request,pk=None):
    Notes.objects.get(id=pk).delete()
    return redirect('notes')


class  NotesDetailView(generic.DetailView):
        model = Notes

@login_required
def homework(request):
    if request.method == 'POST':
        form = HomeWorkForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False
            homeworks =Homework(
                user = request.user,
                subject = request.POST['subject'],
                title = request.POST['title'],
                description = request.POST['description'],
                due = request.POST['due'],
                is_finished = finished
            )
            homeworks.save()
    else:
        form = HomeWorkForm()
    homeworks = Homework.objects.filter(user=request.user)
    if len(homeworks) == 0:
        homework_done = True
    else:
        homework_done = False
    return render(request,'dashboard/homework.html',{'homeworks':homeworks,'homework_done':homework_done,'form':form})


@login_required
def update_homework(request,pk):
    homework = Homework.objects.get(id=pk)
    if homework.is_finished == True:
        homework.is_finished =False
    else:
        homework.is_finished =True
    homework.save()
    return redirect('homework')


@login_required
def delete_homework(request,pk):
    Homework.objects.get(id=pk).delete()
    return redirect('homework')

def youtube(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        video = VideosSearch(text,limit=10)
        result_list = []
        for i in video.result()['result']:
            result_dict ={
                'input':text,
                'title':i['title'],
                'duration':i['duration'],
                'thumbnail':i['thumbnails'][0]['url'],
                'channel':i['channel']['name'],
                'link':i['link'],
                'views':i['viewCount']['short'],
                'published':i['publishedTime']
            }
            desc = ''
            if i['descriptionSnippet']:
                for j in i['descriptionSnippet']:
                    desc += j['text']
            result_dict['description'] = desc
            result_list.append(result_dict)     
        return render(request,'dashboard/youtube.html',{'form':form,'results':result_list})
    else:
        form = DashboardForm()
    return render(request,'dashboard/youtube.html',{'form':form})


@login_required
def todo(request):
    if request.method == 'POST':
        form = TodoForm(request.POST)
        if form.is_valid():
            try:
                finished = request.POST['is_finished']
                if finished == 'on':
                    finished = True
                else:
                    finished = False
            except:
                finished = False 
            todos = Todo(
                user = request.user,
                title = request.POST['title'],
                is_finished = finished
            )
            todos.save()
    else:
        form = TodoForm()
    todo = Todo.objects.filter(user=request.user)
    if len(todo) == 0:
        todos_done = True
    else:
        todos_done = False
    return render(request,'dashboard/todo.html',{'todos':todo,'form':form,'todos_done':todos_done})


@login_required
def update_todo(request,pk):
    todo = Todo.objects.get(id=pk)
    if todo.is_finished == True:
        todo.is_finished = False
    else:
        todo.is_finished = True
    todo.save()
    return redirect('todo')


@login_required
def delete_todo(request,pk):
    Todo.objects.get(id=pk).delete()
    return redirect('todo')



def books(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        url = 'https://www.googleapis.com/books/v1/volumes?q='+text
        r = requests.get(url)
        answer = r.json()
        result_list = []
        for i in range(10):
            image_links = answer['items'][i]['volumeInfo'].get('imageLinks') 
    
            result_dict = {
                'title': answer['items'][i]['volumeInfo']['title'],
                'subtitle': answer['items'][i]['volumeInfo'].get('subtitle'),
                'description': answer['items'][i]['volumeInfo'].get('description'),
                'count': answer['items'][i]['volumeInfo'].get('pageCount'),
                'categories': answer['items'][i]['volumeInfo'].get('categories'),
                'rating': answer['items'][i]['volumeInfo'].get('pageRating'),
                'image_links': image_links,  # Store imageLinks directly
                'thumbnail': image_links.get('thumbnail') if image_links else None,  
                'preview': answer['items'][i]['volumeInfo'].get('previewLink')
            }
            result_list.append(result_dict)     
        return render(request,'dashboard/books.html',{'form':form,'results':result_list})
    else:
        form = DashboardForm()
    return render(request,'dashboard/books.html',{'form':form})

def dictionary(request):
    if request.method == "POST":
        form = DashboardForm(request.POST)
        text = request.POST['text']
        url = "https://api.dictionaryapi.dev/api/v2/entries/en_US/"+text
        r = requests.get(url)
        answer = r.json()
        try:
            phonetics = answer[0]['phonetics'][0]['text']
            audio = answer[0]['phonetics'][0]['audio']
            definition = answer[0]['meanings'][0]['definitions'][0]['definition']
            example = answer[0]['meanings'][0]['definitions'][0]['example']
            synonyms = answer[0]['meanings'][0]['definitions'][0]['synonyms']
            context = {
                'form':form,
                'input':text,
                'phonetics':phonetics,
                'audio':audio,
                'definition':definition,
                'example':example,
                'synonyms':synonyms
            }
        except:
            context = {
                'form':form,
                'input':''
            }
        return render(request,'dashboard/dictionary.html',context)
    else:
        form = DashboardForm()
        context = {'form':form}
    return render(request,'dashboard/dictionary.html',context)


def wiki(request):
    form = DashboardForm(request.POST)
    if request.method == 'POST':
        text = request.POST['text']
    else:
        text = request.GET.get('text','')
    if text:
        try:
            search = wikipedia.page(text)
            context = {
                'form': form,
                'title': search.title,
                'link': search.url,
                'details': search.summary
            }
            return render(request, 'dashboard/wiki.html', context)
        except DisambiguationError as e:
            options = e.options
            context = {
                'form': form,
                'error_message': f"Your search term '{text}' is ambiguous. Please choose from the following options:",
                'options': options
            }
            return render(request, 'dashboard/wiki.html', context)
    context = {
        'form': form,
    }
    return render(request, 'dashboard/wiki.html', context)


def conversion(request):
    if request.method == 'POST':
        form = CoversionForm(request.POST)
        measurement_type = request.POST.get('measurement', '')
        context = {
            'form': form,
            'measurement_type': measurement_type
        }

        if measurement_type == 'length':
            measurement_form = ConversionLengthForm(request.POST)
            context['m_form'] = measurement_form

            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST.get('input')

                if input and input.isdigit():
                    input = int(input)
                    answer = ''
                    if first == 'yard' and second == 'foot':
                        answer = f'{input} yard = {input * 3} foot'
                    elif first == 'foot' and second == 'yard':
                        answer = f'{input} foot = {input / 3} yard'
                    context['answer'] = answer

        elif measurement_type == 'mass':
            measurement_form = ConversionMassForm(request.POST)
            context['m_form'] = measurement_form

            if 'input' in request.POST:
                first = request.POST['measure1']
                second = request.POST['measure2']
                input = request.POST.get('input')

                if input and input.isdigit():
                    input = int(input)
                    answer = ''
                    if first == 'pound' and second == 'kilogram':
                        answer = f'{input} pound = {input * 0.453592} kilogram'
                    elif first == 'kilogram' and second == 'pound':
                        answer = f'{input} kilogram = {input * 2.20462} pound'
                    context['answer'] = answer

    else:
        form = CoversionForm()
        context = {'form': form}

    return render(request, 'dashboard/conversion.html', context)


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request,f"Created {username} account")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request,'dashboard/register.html',{'form':form})


@login_required
def profile(request):
    homeworks = Homework.objects.filter(is_finished=False,user=request.user)
    todos = Todo.objects.filter(is_finished=False,user=request.user)
    if len(homeworks) == 0:
        homeworks_done = True
    else:
        homeworks_done = False
    if len(todos) == 0:
        todos_done = True
    else:
        todos_done = False
    return render(request,'dashboard/profile.html',{'homeworks':homeworks,'todos':todos,'homeworks_done':homeworks_done,'todos_done':todos_done})