from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.core.paginator import Paginator
from django.http import JsonResponse

import random
import time
import re
import PyPDF2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

from .models import Resume, UserSecurity, ActivityLog
from .utils import generate_report

# ✅ Import skill engine
from .skill_learning_db import (
    extract_skills,
    calculate_score,
    predict_roles,
    LEARNING_DB
)

OTP_STORAGE = {}

# ================= PASSWORD CHECK =================
def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    return True


# ================= LOGIN =================
def login_view(request):

    if request.method == "POST":

        username_input = request.POST.get("username")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=username_input)
            username_input = user_obj.username
        except:
            pass

        user = authenticate(request, username=username_input, password=password)

        if user:
            login(request, user)
            ActivityLog.objects.create(user=user, action="User Login")
            return redirect("home")

        messages.error(request, "Invalid credentials")

    return render(request, "users/login.html")


# ================= REGISTER =================

def register(request):

    if request.method == "POST":

        # ===== SEND OTP (AJAX) =====
        if request.POST.get("send_otp"):

            email = request.POST.get("email")

            if not email:
                return JsonResponse({
                    "status": "error",
                    "message": "Enter email first."
                })

            try:
                otp = str(random.randint(100000, 999999))

                OTP_STORAGE[email] = {
                    "otp": otp,
                    "expiry": time.time() + 300
                }

                send_mail(
                    "Registration OTP",
                    f"Your OTP is {otp}. It expires in 5 minutes.",
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )

                return JsonResponse({
                    "status": "success",
                    "message": "OTP sent successfully."
                })

            except Exception as e:
                return JsonResponse({
                    "status": "error",
                    "message": str(e)
                })

        # ===== REGISTER BUTTON =====
        if "register" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            entered_otp = request.POST.get("otp")

            otp_data = OTP_STORAGE.get(email)

            if not otp_data:
                messages.error(request, "Please generate OTP first.")
                return redirect("register")

            if time.time() > otp_data["expiry"]:
                OTP_STORAGE.pop(email, None)
                messages.error(request, "OTP expired. Generate again.")
                return redirect("register")

            if otp_data["otp"] != entered_otp:
                messages.error(request, "Invalid OTP.")
                return redirect("register")

            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return redirect("register")

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )

            OTP_STORAGE.pop(email, None)

            messages.success(request, "Registration successful.")
            return redirect("login")

    return render(request, "users/register.html")

# ================= FORGOT PASSWORD =================
def forgot_password(request):

    if request.method == "POST":

        identifier = request.POST.get("username")

        try:
            if User.objects.filter(email=identifier).exists():
                user = User.objects.get(email=identifier)
            else:
                user = User.objects.get(username=identifier)

        except User.DoesNotExist:
            messages.error(request, "Invalid username or email")
            return redirect("forgot_password")

        otp = str(random.randint(100000, 999999))

        OTP_STORAGE[user.username] = {
            "otp": otp,
            "expiry": time.time() + 300
        }

        send_mail(
            "Password Reset OTP",
            f"Your OTP is {otp}. It expires in 5 minutes.",
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False
        )

        request.session["reset_user"] = user.username
        messages.success(request, "OTP sent to your email")

        return redirect("reset_password")

    return render(request, "users/forgot_password.html")


# ================= RESET PASSWORD =================
def reset_password(request):

    username = request.session.get("reset_user")

    if not username:
        return redirect("login")

    if request.method == "POST":

        otp_entered = request.POST.get("otp")
        new_password = request.POST.get("new_password")

        otp_data = OTP_STORAGE.get(username)

        if not otp_data:
            messages.error(request, "OTP not generated")
            return redirect("forgot_password")

        if time.time() > otp_data["expiry"]:
            OTP_STORAGE.pop(username, None)
            messages.error(request, "OTP expired")
            return redirect("forgot_password")

        if otp_data["otp"] != otp_entered:
            messages.error(request, "Invalid OTP")
            return redirect("reset_password")

        if not is_strong_password(new_password):
            messages.error(request, "Password too weak")
            return redirect("reset_password")

        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()

        OTP_STORAGE.pop(username, None)
        request.session.pop("reset_user", None)

        messages.success(request, "Password reset successful")
        return redirect("login")

    return render(request, "users/reset_password.html")


# ================= HOME =================
@login_required
def home(request):

    latest_resume = Resume.objects.filter(user=request.user).order_by("-uploaded_at").first()
    activities = ActivityLog.objects.filter(user=request.user).order_by("-timestamp")[:5]

    return render(request, "users/home.html", {
        "latest_resume": latest_resume,
        "activities": activities
    })


# ================= UPLOAD RESUME =================
@login_required
def upload_resume(request):

    if request.method == "POST":

        uploaded_file = request.FILES.get("resume")

        if not uploaded_file:
            messages.error(request, "Upload resume first")
            return redirect("upload")

        job_description = request.POST.get("job_description", "")

        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        resume_text = ""

        for page in pdf_reader.pages:
            if page.extract_text():
                resume_text += page.extract_text()

        resume_skills = extract_skills(resume_text)
        jd_skills = extract_skills(job_description)

        matched, missing, coverage, gap = calculate_score(
            resume_skills,
            jd_skills
        )

        score = coverage

        roles = predict_roles(resume_skills)

        suggestions = {
            skill: LEARNING_DB.get(skill, {})
            for skill in missing
        }

        resume_obj = Resume.objects.create(
            user=request.user,
            file=uploaded_file,
            score=score,
            matched_skills=matched,
            missing_skills=missing,
            coverage=coverage,
            gap=gap,
            recommended_roles=roles,
            suggestions=suggestions
        )

        ActivityLog.objects.create(user=request.user, action="Uploaded Resume")

        matched_count = len(matched)
        missing_count = len(missing)

        if matched_count == 0 and missing_count == 0:
            matched_count = 1
            missing_count = 0

        plt.figure(figsize=(5, 5))
        plt.pie(
            [matched_count, missing_count],
            labels=['Matched Skills', 'Missing Skills'],
            autopct='%1.0f%%',
            startangle=90,
            colors=['#22c55e', '#ef4444'],
            wedgeprops={'edgecolor': 'white'}
        )

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)

        chart = base64.b64encode(buffer.getvalue()).decode()
        plt.close()

        return render(request, "users/dashboard.html", {
            "resume": resume_obj,
            "chart": chart,
            "matched": matched,
            "missing": missing,
            "score": score
        })

    return render(request, "users/upload.html")


# ================= HISTORY =================
@login_required
def history(request):

    resumes = Resume.objects.filter(user=request.user).order_by("-uploaded_at")

    paginator = Paginator(resumes, 8)
    page = request.GET.get("page")
    resumes = paginator.get_page(page)

    return render(request, "users/history.html", {"resumes": resumes})


# ================= DELETE =================
@login_required
def delete_resume(request, id):
    resume = get_object_or_404(Resume, id=id, user=request.user)
    resume.delete()
    return redirect("history")


# ================= BULK DELETE =================
@login_required
def bulk_delete(request):
    if request.method == "POST":
        ids = request.POST.getlist("resume_ids")
        Resume.objects.filter(id__in=ids, user=request.user).delete()
    return redirect("history")


# ================= COMPARE =================
@login_required
def compare_resumes(request):
    ids = request.GET.getlist("compare")
    resumes = Resume.objects.filter(id__in=ids, user=request.user)
    return render(request, "users/compare.html", {"resumes": resumes})


# ================= DOWNLOAD REPORT =================
@login_required
def download_report(request, resume_id):

    resume = get_object_or_404(Resume, id=resume_id, user=request.user)

    ActivityLog.objects.create(user=request.user, action="Downloaded Report")

    return generate_report(
        resume.score,
        resume.matched_skills,
        resume.missing_skills,
        resume.suggestions,
        request.user.username,
        resume.recommended_roles,
        resume.coverage,
        resume.gap
    )


# ================= LOGOUT =================
@login_required
def logout_view(request):
    logout(request)
    return redirect("login")