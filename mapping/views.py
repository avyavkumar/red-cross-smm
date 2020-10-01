from django.http import JsonResponse
from django.shortcuts import render, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.hashers import make_password
from django.forms import SelectMultiple
import django_filters
from datetime import date
from mapping.forms import CountryForm, DepartmentForm, TaskForm, SubtaskForm, DescriptionForm, UserForm, UserEditForm
from mapping.models import Country, CustomUser, Department, Task, Subtask, Description
from mapping.filters import DescriptionFilterAdmin, DescriptionFilter

# Create your views here.

def home(request):
    return HttpResponseRedirect('/login')

def login(request):
    # if user is logged in then redirect to the dashboard
    if request.user.is_authenticated():
        if request.user.is_superuser:
            return HttpResponseRedirect('/admin/user')
        return HttpResponseRedirect('/department')

    if request.method == "POST":
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = auth.authenticate(username=username, password=password)
        if user is not None and user.is_active:
            # Login the user
            auth.login(request, user)
            if user.is_superuser:
                return JsonResponse({'message': 'Login Successful', 'redirect': '/admin/user'}, status=200)
            return JsonResponse({'message': 'Login Successful', 'redirect': '/department'}, status=200)
        else:
            return JsonResponse({'message': 'Invalid Username/Password'}, status=500)
    return render(request, 'mapping/login.html')

@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect('/login')

@login_required
def department(request):
    if request.user.is_superuser:
        return HttpResponseRedirect('/admin/user')

    user_department = request.user.department
    return render(request, 'mapping/departments.html', {'department': user_department, 'title':'Departments'})

@login_required
def tasks(request, department=None, task=None):
    if request.user.is_superuser:
        return HttpResponseRedirect('/admin/user')

    user_department = request.user.department
    if int(department) != user_department.id:
        return HttpResponseRedirect('/department')

    subtasks = Subtask.objects.filter(task=task).order_by('name')
    title = Task.objects.get(id=task).name
    return render(request,'mapping/viewtask.html',{'subtasks': subtasks ,'title': title ,'department': user_department})

@login_required
def subtasks(request, department=None, task=None, subtask=None):
    if request.user.is_superuser:
        return HttpResponseRedirect('/admin/user')

    user_department = request.user.department
    if int(department) != user_department.id:
        return HttpResponseRedirect('/department')

    subtasks = Subtask.objects.filter(task=task).order_by('name')
    title = 'Description'
    name = Subtask.objects.get(pk=subtask).name
    try:
        description = Description.objects.filter(subtask=subtask, country=request.user.country).latest('created_at')
    except Description.DoesNotExist:
        description = None
    if request.method == "POST":
        if description:
            form = DescriptionForm(request.POST, instance=description)
        else:
            form = DescriptionForm(request.POST)

        if form.is_valid():
            instance = form.save(commit=False)
            instance.subtask = Subtask.objects.get(id=subtask)
            instance.user = request.user
            instance.country = request.user.country
            instance.save()
            dest_url = '/department/{0}/task/{1}/subtask/{2}'.format(department, task, subtask)
            return HttpResponseRedirect(dest_url, {'success': 'Task Added', 'subtasks': subtasks ,'title': title, 'tasks': tasks , 'form': form, 'name': name})
        else:
            return render(request, 'mapping/viewsubtask.html', {'form': form, 'title': 'Task', 'name': name})
    else:
        if description:
            form = DescriptionForm(instance=description)
        else:
            form = DescriptionForm()
        return render(request,'mapping/viewsubtask.html',{'subtasks': subtasks ,'title': title ,'department': user_department, 'form': form, 'name': name})

@login_required
def listdepartment(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    departments = Department.objects.all().order_by('name')
    return render(request, 'mapping/department_list.html', {'departments': departments , 'title' : 'Departments'})

@login_required
def newdepartment(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/admin/department', {'success': 'Department Added'})
        else:
            return render(request,'mapping/newdepartment.html', {'title': 'Department', 'form': form})
    else:
        form = DepartmentForm()
        return render(request,'mapping/newdepartment.html', {'title': 'Department', 'form': form})

@login_required
def editdepartment(request, id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    department = Department.objects.get(id=id)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/admin/department', {'success': 'Department edited'})
        else:
            return render(request,'mapping/newdepartment.html', {'title': 'Department', 'form': form})
    else:
        form = DepartmentForm(instance=department)
        return render(request,'mapping/newdepartment.html', {'title': 'Department', 'form': form})

@login_required
def listtask(request,id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    tasks = Task.objects.filter(department=id)
    return render(request, 'mapping/task_list.html', {'tasks': tasks, 'department_id':id , 'title' : 'Tasks'})

@login_required
def listsubtask(request, department_id=None, task_id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    subtasks = Subtask.objects.filter(task__id=task_id)
    return render(request, 'mapping/subtask_list.html', {'subtasks': subtasks, 'department_id':department_id, 'task_id':task_id , 'title' : 'Subtasks'})

@login_required
def newsubtask(request, department_id=None, task_id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    if request.method == "POST":
        form = SubtaskForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.task = Task.objects.get(id=task_id)
            instance.save()
            return HttpResponseRedirect('/admin/department/{0}/task/{1}/subtask'.format(department_id, task_id), {'success': 'Task Added'})
        else:
            return render(request,'mapping/newsubtask.html',{'title':'NEW TASK ', 'tasks': tasks , 'form' : form, 'department_id': department_id, 'task_id': task_id})

    else:
        form = SubtaskForm()
        return render(request,'mapping/newsubtask.html',{ 'title':'NEW SUBTASK ','tasks': tasks , 'form' : form, 'department_id': department_id, 'task_id': task_id})

@login_required
def editsubtask(request, department_id=None, task_id=None, subtask_id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    subtask = Subtask.objects.get(id=subtask_id)
    if request.method == 'POST':
        form = SubtaskForm(request.POST, instance=subtask)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/admin/department/{0}/task/{1}/subtask'.format(department_id, task_id), {'success': 'Task edited'})
        else:
            return render(request,'mapping/editsubtask.html', {'title': 'Department', 'form': form, 'department_id': department_id, 'task_id': task_id, 'subtask_id': subtask_id})
    else:
        form = SubtaskForm(instance=subtask)
        return render(request,'mapping/editsubtask.html', {'title': 'Department', 'form': form , 'department_id': department_id, 'task_id': task_id, 'subtask_id': subtask_id})

@login_required
def newtask(request,id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.department = Department.objects.get(id=id)
            instance.save()
            return HttpResponseRedirect('/admin/department/{0}/task'.format(id), {'success': 'Task Added'})
        else:
            return render(request,'mapping/newtask.html',{'title':'NEW TASK ', 'department_id': id, 'tasks': tasks , 'form' : form})

    else:
        form = TaskForm()
        return render(request,'mapping/newtask.html',{ 'title':'NEW TASK ','department_id': id ,'tasks': tasks , 'form' : form})

@login_required
def edittask(request, department=None,task=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    tasks = Task.objects.get(id=task)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=tasks)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/admin/department/{0}/task'.format(department), {'success': 'Task edited'})
        else:
            return render(request,'mapping/edittask.html', {'title': 'Department', 'form': form, 'department_id': department ,'task_id' : task })
    else:
        form = TaskForm(instance=tasks)
        return render(request,'mapping/edittask.html', {'title': 'Department', 'form': form , 'department_id': department,'task_id' : task })

@login_required
def filter_admin(request):
    f = DescriptionFilterAdmin(request.POST, queryset=Description.objects.all())

    if request.method == 'POST':
        countries = [c.name for c in Country.objects.filter(pk__in=request.POST.getlist('country'))]
        subtasks = [s.name for s in Subtask.objects.filter(pk__in=request.POST.getlist('subtask'))]

        descriptions = {}
        for obj in f:
            if obj.country.name in descriptions:
                descriptions[obj.country.name][obj.subtask.name] = [obj.description, obj.status]
            else:
                descriptions[obj.country.name] = {obj.subtask.name: [obj.description, obj.status]}

        return render(request, 'mapping/print.html', {'descriptions': descriptions, 'countries': countries, 'subtasks': subtasks})
    return render(request, 'mapping/filter_admin.html', {'filter': f, 'title': 'Filter'})

@login_required
def filter(request):
    f = DescriptionFilter(data=request.POST, queryset=Description.objects.filter(country=request.user.country, subtask__task__department=request.user.department), department=request.user.department)

    if request.method == 'POST':
        subtasks = [s.name for s in Subtask.objects.filter(pk__in=request.POST.getlist('subtask'))]

        descriptions = {}
        countries = [request.user.country.name]
        for obj in f:
            if obj.country.name in descriptions:
                descriptions[obj.country.name][obj.subtask.name] = [obj.description, obj.status]
            else:
                descriptions[obj.country.name] = {obj.subtask.name: [obj.description, obj.status]}

        return render(request, 'mapping/print.html', {'descriptions': descriptions, 'countries': countries, 'subtasks': subtasks})
    return render(request, 'mapping/filter.html', {'filter': f, 'title': 'Filter'})

@login_required
def user(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    u = CustomUser.objects.all().order_by('country')
    return render(request, 'mapping/user_list.html', {'title': 'Users', 'users': u})

@login_required
def newuser(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user')
        else:
            return render(request, 'mapping/newuser.html', {'title': 'User', 'form': form})
    else:
        form = UserForm()
        return render(request, 'mapping/newuser.html', {'title': 'User', 'form': form})

@login_required
def edituser(request, id=None):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/department')

    user = CustomUser.objects.get(id=id)
    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/user', {'success': 'User Updated'})
        else:
            return render(request, 'mapping/edituser.html', {'id': user.id, 'form': form, 'title': 'Users'})
    else:
        form = UserEditForm(instance=user)
        return render(request,'mapping/edituser.html', {'id': user.id, 'form': form, 'title': 'Users'})

@login_required
def changepassword(request):
    if request.method == 'POST':
        form = PasswordChangeForm(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            auth.update_session_auth_hash(request, form.user)
            if request.user.is_superuser:
                return HttpResponseRedirect('/admin/user')
            return HttpResponseRedirect('/department')
        else:
            if request.user.is_superuser:
                return render(request, 'mapping/changepassword_admin.html', {'form': form, 'title': 'Change Password'})
            return render(request, 'mapping/changepassword.html', {'form': form})
    else:
        form = PasswordChangeForm(user=request.user)
        if request.user.is_superuser:
            return render(request, 'mapping/changepassword_admin.html', {'form': form, 'title': 'Change Password'})
        return render(request, 'mapping/changepassword.html', {'form': form, 'title': 'Change Password'})
