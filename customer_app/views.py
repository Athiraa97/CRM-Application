from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse, Http404
from .models import Customer
from .forms import CustomerForm, ExcelUploadForm, UserForm
import pandas as pd
from reportlab.lib.pagesizes import letter
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


def home_view(request):
    try:
        if request.user.is_authenticated:
            return redirect('customer_list')
        return redirect('login')
    except Exception as e:
        return HttpResponse(f"Error in home view: {e}", status=500)


def login_view(request):
    try:
        if request.user.is_authenticated:
            return redirect('customer_list')
        error = ''
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('customer_list')
            else:
                error = 'Invalid credentials'
        return render(request, 'login.html', {'error': error})
    except Exception as e:
        return HttpResponse(f"Error in login view: {e}", status=500)


@login_required
def logout_view(request):
    try:
        logout(request)
        return redirect('login')
    except Exception as e:
        return HttpResponse(f"Error in logout view: {e}", status=500)


# --- Customer CRUD ---

@login_required
def customer_list(request):
    try:
        customers = Customer.objects.all().order_by('-created_at')
        return render(request, 'customer_list.html', {'customers': customers})
    except Exception as e:
        return render(request, 'customer_list.html', {'customers': [], 'error': f"Error: {e}"})


@login_required
def customer_create(request):
    try:
        if request.method == 'POST':
            form = CustomerForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect('customer_list')
        else:
            form = CustomerForm()
        return render(request, 'customer_form.html', {'form': form, 'action': 'Add'})
    except Exception as e:
        return HttpResponse(f"Error creating customer: {e}", status=500)


@login_required
def customer_edit(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        if request.method == 'POST':
            form = CustomerForm(request.POST, request.FILES, instance=customer)
            if form.is_valid():
                form.save()
                return redirect('customer_list')
        else:
            form = CustomerForm(instance=customer)
        return render(request, 'customer_form.html', {'form': form, 'action': 'Edit'})
    except Exception as e:
        return HttpResponse(f"Error editing customer: {e}", status=500)


@login_required
def customer_delete(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        if request.method == 'POST':
            customer.delete()
            return redirect('customer_list')
        return render(request, 'customer_detail.html', {'customer': customer, 'confirm_delete': True})
    except Exception as e:
        return HttpResponse(f"Error deleting customer: {e}", status=500)


@login_required
def customer_detail(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        return render(request, 'customer_detail.html', {'customer': customer})
    except Exception as e:
        raise Http404(f"Error loading customer: {e}")


# --- Bulk upload from Excel ---
@login_required
def customer_bulk_upload(request):
    try:
        message = ''
        if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)
            if form.is_valid():
                excel = request.FILES['excel_file']
                try:
                    df = pd.read_excel(excel)
                    for _, row in df.fillna('').iterrows():
                        Customer.objects.create(
                            first_name=row.get('first_name') or row.get('First Name') or '',
                            last_name=row.get('last_name') or row.get('Last Name') or '',
                            email=row.get('email') or '',
                            phone=str(row.get('phone') or ''),
                            city=row.get('city') or '',
                            state=row.get('state') or '',
                            country=row.get('country') or '',
                        )
                    message = 'Customers imported successfully.'
                except Exception as e:
                    message = f'Error processing file: {e}'
        else:
            form = ExcelUploadForm()
        return render(request, 'customer_list.html', {
            'bulk_form': form,
            'message': message,
            'customers': Customer.objects.all().order_by('-created_at')
        })
    except Exception as e:
        return HttpResponse(f"Error bulk uploading customers: {e}", status=500)


@login_required
def download_customers_pdf(request):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)

        styles = getSampleStyleSheet()
        story = [Paragraph("<b>Customers Report</b>", styles["Title"]), Spacer(1, 20)]

        customers = Customer.objects.all().order_by("first_name")
        for c in customers:
            if c.image:
                try:
                    img = Image(c.image.path, width=80, height=80)
                except Exception:
                    img = Paragraph("No Image", styles["Normal"])
            else:
                img = Paragraph("No Image", styles["Normal"])

            details = [
                ["Name:", f"{c.first_name} {c.last_name}"],
                ["Email:", c.email or "—"],
                ["Phone:", c.phone or "—"],
                ["Address:", f"{c.city or ''}, {c.state or ''}, {c.country or ''}"],
            ]
            table = Table(details, colWidths=[80, 350])
            table.setStyle(TableStyle([
                ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.darkblue),
            ]))

            profile_row = Table([[img, table]], colWidths=[90, 400])
            profile_row.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ]))

            story.append(profile_row)
            story.append(Spacer(1, 20))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="customers.pdf"'
        response.write(pdf)
        return response
    except Exception as e:
        return HttpResponse(f"Error generating customers PDF: {e}", status=500)


@login_required
def download_customer_pdf_individual(request, pk):
    try:
        customer = get_object_or_404(Customer, pk=pk)
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                rightMargin=40, leftMargin=40, topMargin=60, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = [Paragraph("<b>Customer Profile</b>", styles["Title"]), Spacer(1, 20)]

        if customer.image:
            try:
                img = Image(customer.image.path, width=100, height=100)
            except Exception:
                img = Paragraph("No Image", styles["Normal"])
        else:
            img = Paragraph("No Image", styles["Normal"])

        details = [
            ["Name:", f"{customer.first_name} {customer.last_name}"],
            ["Email:", customer.email or "—"],
            ["Phone:", customer.phone or "—"],
            ["Address:", f"{customer.city or ''}, {customer.state or ''}, {customer.country or ''}"],
        ]
        table = Table(details, colWidths=[80, 350])
        table.setStyle(TableStyle([
            ("BOX", (0, 0), (-1, -1), 0.25, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ]))

        profile_row = Table([[img, table]], colWidths=[110, 400])
        profile_row.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ]))

        story.append(profile_row)
        story.append(Spacer(1, 20))

        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="customer_{customer.pk}.pdf"'
        response.write(pdf)
        return response
    except Exception as e:
        return HttpResponse(f"Error generating customer PDF: {e}", status=500)


# --- User Management ---

@login_required
def user_list(request):
    try:
        users = User.objects.all().order_by('-is_staff', 'username')
        return render(request, 'user_list.html', {'users': users})
    except Exception as e:
        return HttpResponse(f"Error fetching users: {e}", status=500)


@login_required
def user_add(request):
    try:
        if request.method == 'POST':
            form = UserForm(request.POST)
            if form.is_valid():
                data = form.save(commit=False)
                password = form.cleaned_data.get('password')
                if password:
                    data.set_password(password)

                role = form.cleaned_data.get('role')
                if role == 'admin':
                    data.is_superuser = True
                    data.is_staff = True
                elif role == 'team_lead':
                    data.is_superuser = False
                    data.is_staff = True
                else:
                    data.is_superuser = False
                    data.is_staff = False

                data.save()
                return redirect('user_list')
        else:
            form = UserForm()
        return render(request, 'user_form.html', {'form': form, 'action': 'Add'})
    except Exception as e:
        return HttpResponse(f"Error adding user: {e}", status=500)


@login_required
def user_edit(request, pk):
    try:
        user = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            form = UserForm(request.POST, instance=user)
            if form.is_valid():
                data = form.save(commit=False)
                password = form.cleaned_data.get('password')
                if password:
                    data.set_password(password)

                role = form.cleaned_data.get('role')
                if role == 'admin':
                    data.is_superuser = True
                    data.is_staff = True
                elif role == 'team_lead':
                    data.is_superuser = False
                    data.is_staff = True
                else:
                    data.is_superuser = False
                    data.is_staff = False

                data.save()
                return redirect('user_list')
        else:
            initial_role = 'user'
            if user.is_superuser:
                initial_role = 'admin'
            elif user.is_staff:
                initial_role = 'team_lead'
            form = UserForm(instance=user, initial={'role': initial_role})
        return render(request, 'user_form.html', {'form': form, 'action': 'Edit'})
    except Exception as e:
        return HttpResponse(f"Error editing user: {e}", status=500)


@login_required
def edit_profile(request):
    try:
        user = request.user
        if request.method == 'POST':
            form = UserForm(request.POST, instance=user)
            if form.is_valid():
                data = form.save(commit=False)
                password = form.cleaned_data.get('password')
                if password:
                    data.set_password(password)
                data.save()
                return redirect('customer_list')
        else:
            form = UserForm(instance=user)
        return render(request, 'edit_profile.html', {'form': form})
    except Exception as e:
        return HttpResponse(f"Error editing profile: {e}", status=500)


@login_required
def user_detail(request, pk):
    try:
        users = get_object_or_404(User, pk=pk)
        return render(request, 'user_detail.html', {'users': users})
    except Exception as e:
        raise Http404(f"Error loading user: {e}")


@login_required
def user_delete(request, pk):
    try:
        users = get_object_or_404(User, pk=pk)
        if request.method == 'POST':
            users.delete()
            return redirect('user_list')
        return render(request, 'user_detail.html', {'users': users, 'confirm_delete': True})
    except Exception as e:
        return HttpResponse(f"Error deleting user: {e}", status=500)
