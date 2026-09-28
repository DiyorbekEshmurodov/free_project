from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import FitnessPlan
from .forms import FitnessPlanForm
from apps.accounts.services import get_user_profile
from .ai_api import generate_user_advice as ai_generate_advice

# GET parametrlarini tekshirish uchun oq ro'yxat (Whitelist - B6 himoyasi)
ALLOWED_CARDS = {'weight_loss', 'muscle_gain', 'stamina', 'health_habits'}
ALLOWED_PERIODS = {'daily', 'weekly', 'monthly', 'yearly'}


def profile_required(view_func):
    """Profil topilmasa profile_setup'ga yo'naltiruvchi dekorator (DRY)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile = get_user_profile(request.user)
        if not profile:
            return redirect('profile_setup')
        request.profile = profile
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
@profile_required
def plan_list(request):
    period = request.GET.get('period', 'daily')
    if period not in ALLOWED_PERIODS:
        period = 'daily'

    plans = FitnessPlan.objects.filter(user=request.profile, period_type=period).order_by('target_date')

    ctx = {
        'plans': plans,
        'period': period
    }
    return render(request, "fitness_app/list.html", ctx)


@login_required
@profile_required
def plan_create(request):
    form = FitnessPlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.user = request.profile
        plan.save()
        return redirect('user_list')
    return render(request, 'fitness_app/form.html', {'form': form})


@login_required
@profile_required
def plan_edit(request, pk):
    plan = get_object_or_404(FitnessPlan, pk=pk, user=request.profile)
    form = FitnessPlanForm(request.POST or None, instance=plan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('user_list')
    return render(request, 'fitness_app/form.html', {'form': form})


@login_required
@require_POST
@profile_required
def plan_delete(request, pk):
    plan = get_object_or_404(FitnessPlan, pk=pk, user=request.profile)
    plan.delete()
    return redirect('user_list')


def user_plan(request):
    context = {
        'has_profile': get_user_profile(request.user) is not None,
    }
    return render(request, 'index.html', context)


class AIReportView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness_app/reports.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.profile = get_user_profile(request.user)
            if request.profile is None:
                return redirect('profile_setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cards = [
            {'id': 'weight_loss', 'icon': '🔥', 'title': "Vazn tashlash va yog' eritish",
             'desc': "Kaloriya defitsiti va yog' yoqish rejasi."},
            {'id': 'muscle_gain', 'icon': '💪', 'title': "Mushak massasini oshirish",
             'desc': "Gipertrofiya va oqsilga boy ratsion."},
            {'id': 'stamina', 'icon': '⚡', 'title': "Chidamlilik va Energiya",
             'desc': "Kun davomida tetiklik va quvvatni oshirish."},
            {'id': 'health_habits', 'icon': '🥗', 'title': "Sog'lom turmush tarzi",
             'desc': "Kunlik to'g'ri odatlarni shakllantirish."}
        ]
        context['cards'] = cards
        # dispatch'da olingan profilni qayta ishlatamiz (C2 optimizatsiya)
        profil = getattr(self.request, 'profile', get_user_profile(self.request.user))
        context['profil'] = profil
        context['has_profile'] = profil is not None

        return context


class AIPageDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness_app/ai_page.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            request.profile = get_user_profile(request.user)
            if request.profile is None:
                return redirect('profile_setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = getattr(self.request, 'profile', get_user_profile(self.request.user))

        # Parametrlarni oq ro'yxat orqali xavfsiz saralash (B6 himoyasi)
        card_param = self.request.GET.get('card')
        selected_card = card_param if card_param in ALLOWED_CARDS else 'weight_loss'

        period_param = self.request.GET.get('period')
        selected_period = period_param if period_param in ALLOWED_PERIODS else 'weekly'

        period_titles = {
            'daily': 'Kunlik',
            'weekly': 'Haftalik',
            'monthly': 'Oylik',
            'yearly': 'Yillik'
        }
        period_label = period_titles.get(selected_period, 'Haftalik')

        # Groq AI maslahatini olish
        advice_data = ai_generate_advice(profile, selected_card, selected_period)

        # Diagramma ma'lumotlari
        chart_data = self.get_chart_data(selected_period, selected_card)

        context.update({
            'selected_card': selected_card,
            'selected_period': selected_period,
            'period_label': period_label,
            'advice_data': advice_data,
            'chart_data': chart_data,
            'profile': profile,
        })
        return context

    def get_chart_data(self, period, card_id):
        if period == 'daily':
            labels = ['08:00 (Ertalab)', '12:00 (Tushlik)', '16:00 (Poldnik)', '20:00 (Kechki)']
            scores = [20, 45, 75, 100]
        elif period == 'weekly':
            labels = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
            scores = [10, 25, 40, 60, 75, 85, 100]
        elif period == 'monthly':
            labels = ['1-Hafta', '2-Hafta', '3-Hafta', '4-Hafta']
            scores = [15, 40, 70, 100]
        else:
            labels = ['1-Chorak', '2-Chorak', '3-Chorak', '4-Chorak']
            scores = [20, 50, 80, 100]

        return {'labels': labels, 'scores': scores}