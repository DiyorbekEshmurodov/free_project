from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import FitnessPlan
from .forms import FitnessPlanForm
from accounts.models import UserDetail


@login_required
def plan_list(request):
    profile = UserDetail.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile_setup')
    period = request.GET.get('period', 'daily')
    plans = FitnessPlan.objects.filter(user=profile, period_type=period).order_by('target_date')

    ctx = {
        'plans': plans,
        'period': period
    }
    return render(request, "fitness_app/list.html", ctx)


@login_required
def plan_create(request):
    profile = UserDetail.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile_setup')
    form = FitnessPlanForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        plan = form.save(commit=False)
        plan.user = profile
        plan.save()
        return redirect('user_list')
    return render(request, 'fitness_app/form.html', {'form': form})


@login_required
def plan_edit(request, pk):
    profile = UserDetail.objects.filter(user=request.user).first()
    if not profile :
        return redirect('profile_setup')
    plan = get_object_or_404(FitnessPlan, pk=pk, user=profile)
    form = FitnessPlanForm(request.POST or None, instance=plan)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('user_list')
    return render(request, 'fitness_app/form.html', {'form': form})


@login_required
def plan_delete(request, pk):
    profile  = UserDetail.objects.filter(user=request.user).first()
    if not profile:
        return redirect('profile_setup')
    plan = get_object_or_404(FitnessPlan, pk=pk, user=profile)
    plan.delete()
    return redirect('user_list')


def user_plan(request):
    has_profile = False
    if request.user.is_authenticated:
        has_profile = UserDetail.objects.filter(user=request.user).exists()

    context = {
        'has_profile': has_profile,
    }
    return render(request, 'index.html', context)


class AIReportView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness_app/reports.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not UserDetail.objects.filter(user=request.user).exists():
            return redirect('profile_setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cards = [
            {'id': 'weight_loss', 'icon': '🔥', 'title': "Vazn tashlash va yog' eritish", 'desc': "Kaloriya defitsiti va yog' yoqish rejasi."},
            {'id': 'muscle_gain', 'icon': '💪', 'title': "Mushak massasini oshirish", 'desc': "Gipertrofiya va oqsilga boy ratsion."},
            {'id': 'stamina', 'icon': '⚡', 'title': "Chidamlilik va Energiya", 'desc': "Kun davomida tetiklik va quvvatni oshirish."},
            {'id': 'health_habits', 'icon': '🥗', 'title': "Sog'lom turmush tarzi", 'desc': "Kunlik to'g'ri odatlarni shakllantirish."}
        ]
        context['cards'] = cards
        profil = UserDetail.objects.filter(user=self.request.user).first()
        context['profil'] = profil
        context['has_profile'] = profil is not None

        return context



class AIPageDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'fitness_app/ai_page.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not UserDetail.objects.filter(user=request.user).exists():
            return redirect('profile_setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = UserDetail.objects.filter(user=self.request.user).first()

        selected_card = self.request.GET.get('card', 'weight_loss')
        selected_period = self.request.GET.get('period', 'weekly')

        # Davr nomini o'zbekcha matnga o'girish
        period_titles = {
            'daily': 'Kunlik',
            'weekly': 'Haftalik',
            'monthly': 'Oylik',
            'yearly': 'Yillik'
        }
        period_label = period_titles.get(selected_period, 'Haftalik')

        # Kengaytirilgan AI Maslahati
        advice_data = self.generate_user_advice(profile, selected_card, selected_period)

        # Diagramma (Graph) uchun dinamik ma'lumotlar
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
        # Tanlangan davrga qarab grafik x-o'qi va y-o'qi ko'rsatkichlari
        if period == 'daily':
            labels = ['08:00 (Ertalab)', '12:00 (Tushlik)', '16:00 (Poldnik)', '20:00 (Kechki)']
            scores = [20, 45, 75, 100]
        elif period == 'weekly':
            labels = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
            scores = [10, 25, 40, 60, 75, 85, 100]
        elif period == 'monthly':
            labels = ['1-Hafta', '2-Hafta', '3-Hafta', '4-Hafta']
            scores = [15, 40, 70, 100]
        else: # yearly
            labels = ['1-Chorak', '2-Chorak', '3-Chorak', '4-Chorak']
            scores = [20, 50, 80, 100]

        return {'labels': labels, 'scores': scores}

    def generate_user_advice(self, profile, card_id, period):
        if not profile:
            return {}

        vazni = getattr(profile, 'vazni', '70')
        boyi = getattr(profile, 'boyi', '175')
        try:
            vazn_num = float(vazni)
        except (ValueError, TypeError):
            vazn_num = 70.0

        p_name = {'daily': 'kunlik', 'weekly': 'haftalik', 'monthly': 'oylik', 'yearly': 'yillik'}.get(period, 'haftalik')

        # Har bir karta va davr uchun batafsil reja
        if card_id == 'weight_loss':
            return {
                'nutrition': f"Sizning {p_name} ratsioningiz: Kuniga kamida {vazn_num * 35 / 1000:.1f}L suv iching. Shirinlik va xamir ovqatlarni butunlay cheklab, har bir taomlanishda 30g oqsil (tovuq go'shti, tuxum, tvorog) va murakkab uglevodlar (guruch, grechka) iste'mol qiling.",
                'workout': f"Sizning {p_name} mashg'ulot rejangiz: Boshlanishiga {p_name} 3-4 marta kardio (30 daqiqa yugurish yoki tez yurish) hamda umumiy tana mushaklarini mustahkamlovchi yengil kuch mashqlarini bajaring.",
                'ai_recommendation': f"Boyingiz {boyi} sm va vazningiz {vazni} kg bo'lgani uchun, metabolizmni ushlab turish muhim. Oqsillar balansi va 8 soatlik sifatli uyqu {p_name} rejangizning asosiy kalitidir.",
                'timeline': f"Ushbu {p_name} rejaga qat'iy amal qilsangiz, belgilangan vaqt davomida yog' foizini 2-4% ga kamaytirish va umumiy energiyani oshirish kafolatlanadi."
            }
        elif card_id == 'muscle_gain':
            return {
                'nutrition': f"Sizning {p_name} gipertrofiya ratsioningiz: Kunlik {vazn_num * 1.8:.0f}g oqsil qabul qiling. Kaloriya miqdorini normadan 300 kcal ga oshiring. Mol go'shti, baliq, tuxum va yong'oqlarga urg'u bering.",
                'workout': f"Sizning {p_name} mashg'ulot rejangiz: Og'ir vaznlar bilan 8-12 marta qaytariladigan bazaviy mashqlarni bajaring (Jim leja, Pritsed, Stanovaya tyaga). Har bir mashq orasida 2 daqiqa dam oling.",
                'ai_recommendation': f"Vazn {vazni} kg ko'rsatkichida mushak o'sishi uchun har bir mushak guruhiga mashqdan so'ng kamida 48 soat tiklanish vaqti bering.",
                'timeline': f"{p_name.capitalize()} natija: Mushak hajmining sezilarli darajada kattalashishi hamda kuch ko'rsatkichlarining 15-20% ga oshishi."
            }
        elif card_id == 'stamina':
            return {
                'nutrition': f"Sizning {p_name} energiya ratsioningiz: Antioksidantlarga boy mahsulotlar (suyak sho'rva, mevalar, ko'katlar) va yetarli miqdorda kaliy/magniy moddalarini qabul qiling.",
                'workout': f"Sizning {p_name} mashq rejangiz: Tabata va HIIT (Yuqori intensivli) mashqlarini bajaring. Yugurish masofasini va sur'atini {p_name} bosqichma-bosqich oshirib boring.",
                'ai_recommendation': "Nafas olish va yurak urish maromini (puls) nazorat qiling. Mashq paytida suvsizlanishga yo'l qo'ymang.",
                'timeline': f"{p_name.capitalize()} natija: Nafas qisishi yo'qolishi, quvvat darajasi va chidamlilikning maksimumga chiqishi."
            }
        else: # health_habits
            return {
                'nutrition': f"Sizning {p_name} sog'lom ratsioningiz: Ishlov berilgan (fast-food, gazli ichimliklar) mahsulotlarni to'xtating. Har bir taomga yangi uzilgan sabzavotlar qo'shing.",
                'workout': f"Sizning {p_name} odat rejangiz: Kuniga kamida 8,000-10,000 qadam piyoda yuring, ertalabki 10 daqiqalik badan tarbiya va stretching mashqlarini bajaring.",
                'ai_recommendation': "Kun tartibiga amal qiling: Har kuni bir xil vaqtda uxlash va bir xil vaqtda uyg'onishni odat qiling.",
                'timeline': f"{p_name.capitalize()} natija: Uyqu sifatining yaxshilanishi, hazm qilish tizimi normallashishi va kayfiyat barqarorligi."
            }