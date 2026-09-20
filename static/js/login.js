/* Parolni ko'rsatish/yashirish funksiyasi */
function togglePasswordVisibility(inputId, icon) {
    const input = document.getElementById(inputId);
    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = '🙈';
    } else {
        input.type = 'password';
        icon.textContent = '👁️';
    }
}

/* Telefon raqamini avtomatik maskalash (+998 90-123-45-67) */
function formatPhoneNumber(input) {
    let numbers = input.value.replace(/\D/g, '');

    if (numbers.startsWith('998')) {
        numbers = numbers.substring(3);
    }

    numbers = numbers.substring(0, 9);

    let result = '+998 ';

    if (numbers.length > 0) {
        result += numbers.substring(0, 2);
    }
    if (numbers.length >= 3) {
        result += '-' + numbers.substring(2, 5);
    }
    if (numbers.length >= 6) {
        result += '-' + numbers.substring(5, 7);
    }
    if (numbers.length >= 8) {
        result += '-' + numbers.substring(7, 9);
    }

    input.value = numbers.length > 0 ? result : '';
}

/* Parol murakkabligini dinamik tekshirish */
function checkPasswordStrength() {
    const password = document.getElementById('password').value;

    const reqLength = document.getElementById('req-length');
    const reqUpper = document.getElementById('req-uppercase');
    const reqLower = document.getElementById('req-lowercase');

    // 1. Kamida 8 ta belgi
    if (password.length >= 8) {
        reqLength.className = 'req-item valid';
        reqLength.querySelector('.req-icon').textContent = '✔';
    } else {
        reqLength.className = 'req-item invalid';
        reqLength.querySelector('.req-icon').textContent = '✖';
    }

    // 2. Katta harf (A-Z)
    if (/[A-Z]/.test(password)) {
        reqUpper.className = 'req-item valid';
        reqUpper.querySelector('.req-icon').textContent = '✔';
    } else {
        reqUpper.className = 'req-item invalid';
        reqUpper.querySelector('.req-icon').textContent = '✖';
    }

    // 3. Kichik harf (a-z)
    if (/[a-z]/.test(password)) {
        reqLower.className = 'req-item valid';
        reqLower.querySelector('.req-icon').textContent = '✔';
    } else {
        reqLower.className = 'req-item invalid';
        reqLower.querySelector('.req-icon').textContent = '✖';
    }
}

/* Tablarni almashtirish funksiyasi */
function switchTab(mode) {
    const phoneGroup = document.getElementById('phone-group');
    const confirmPassGroup = document.getElementById('confirm-pass-group');
    const passRequirements = document.getElementById('password-requirements');
    const forgotBox = document.getElementById('forgot-link-box');
    const title = document.getElementById('form-title');
    const subtitle = document.getElementById('form-subtitle');
    const submitBtn = document.getElementById('submit-btn');
    const actionType = document.getElementById('action_type');

    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');

    if (mode === 'login') {
        phoneGroup.style.display = 'none';
        confirmPassGroup.style.display = 'none';
        passRequirements.style.display = 'none';
        forgotBox.style.display = 'block';

        title.textContent = "Tizimga kirish";
        subtitle.textContent = "Ma'lumotlaringizni to'g'ri kiriting";
        submitBtn.textContent = "Tizimga kirish";
        actionType.value = "login";

        tabLogin.classList.add('active');
        tabRegister.classList.remove('active');

    } else if (mode === 'register') {
        phoneGroup.style.display = 'block';
        confirmPassGroup.style.display = 'block';
        passRequirements.style.display = 'block';
        forgotBox.style.display = 'none';

        title.textContent = "Ro'yxatdan o'tish";
        subtitle.textContent = "Yangi hisob yaratish uchun to'ldiring";
        submitBtn.textContent = "Ro'yxatdan o'tish";
        actionType.value = "register";

        tabRegister.classList.add('active');
        tabLogin.classList.remove('active');

    } else if (mode === 'reset') {
        phoneGroup.style.display = 'block';
        confirmPassGroup.style.display = 'block';
        passRequirements.style.display = 'block';
        forgotBox.style.display = 'none';

        title.textContent = "Parolni tiklash";
        subtitle.textContent = "Telefon va yangi parolni kiriting";
        submitBtn.textContent = "Parolni yangilash";
        actionType.value = "reset";

        tabLogin.classList.remove('active');
        tabRegister.classList.remove('active');
    }
}