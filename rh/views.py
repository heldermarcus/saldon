from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Employee
from .forms import EmployeeForm
from financial.models import Sale
from core.models import Store
from django.db.models import Sum
from datetime import datetime

@login_required
def employee_list(request):
    store = request.user.stores.first()
    if not store:
        messages.error(request, 'Você precisa criar uma loja primeiro.')
        return redirect('dashboard')
    
    employees = Employee.objects.filter(store=store)
    return render(request, 'rh/employee_list.html', {'employees': employees})

@login_required
def employee_create(request):
    store = request.user.stores.first()
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            employee.store = store
            employee.save()
            messages.success(request, 'Funcionário cadastrado com sucesso!')
            return redirect('rh:employee_list')
    else:
        form = EmployeeForm()
    return render(request, 'rh/employee_form.html', {'form': form, 'title': 'Novo Funcionário'})

@login_required
def employee_update(request, pk):
    store = request.user.stores.first()
    employee = get_object_or_404(Employee, pk=pk, store=store)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário atualizado com sucesso!')
            return redirect('rh:employee_list')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'rh/employee_form.html', {'form': form, 'title': 'Editar Funcionário'})

@login_required
def rh_dashboard(request):
    store = request.user.stores.first()
    if not store:
        return redirect('dashboard')
        
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    employees = Employee.objects.filter(store=store)
    
    # Calculate performance for each employee in the current month
    employee_performance = []
    for emp in employees:
        sales = Sale.objects.filter(
            employee=emp, 
            store=store,
            sale_date__month=current_month,
            sale_date__year=current_year
        )
        total_sales = sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        sales_count = sales.count()
        employee_performance.append({
            'employee': emp,
            'total_sales': total_sales,
            'sales_count': sales_count
        })
        
    # Sort by total sales descending
    employee_performance.sort(key=lambda x: x['total_sales'], reverse=True)
    
    context = {
        'employee_performance': employee_performance,
        'current_month_name': datetime.now().strftime('%B'),
    }
    return render(request, 'rh/dashboard.html', context)
