const nickname = document.getElementById('input_login_nickname');
const password = document.getElementById('input_login_password');
const loginButton = document.getElementById('btn_login');

document.addEventListener('DOMContentLoaded', function () {
    function validateForm() {
        // Проверяем, заполнены ли все поля и отмечен ли чекбокс
        const isFormValid = nickname.value.trim() !== '' &&
                            password.value.trim() !== '';
        // Включаем или отключаем кнопку в зависимости от состояния формы
        loginButton.disabled = !isFormValid;
    }

    // Привязываем событие 'input' ко всем полям для проверки формы в реальном времени
    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);

    validateForm();
});

async function login_account() {
    const result = await window.pywebview.api.account_login(nickname.value, password.value);

    if (Array.isArray(result)) {
        if (result[3]) {
            open_tab("index.html")
        } else {
            open_tab("link_discord_register.html")
        }
    } else {
        if (result === 401) {
            showErrorModal("Неверный логин или пароль.");
        } else {
            showErrorModal("Произошла непредвиденная ошибка. Попробуйте еще раз.");
        }
    }
}

loginButton.addEventListener("click", function () {
    login_account();
})