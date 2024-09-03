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

loginButton.addEventListener("click", function () {
    window.pywebview.api.account_login(nickname.value, password.value);
})