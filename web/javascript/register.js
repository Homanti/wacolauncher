const nickname = document.getElementById('input_register_nickname');
const password = document.getElementById('input_register_password');
const history = document.getElementById('input_register_history');
const how_did_you_find = document.getElementById('input_register_how_did_you_find');
const skin = document.getElementById('input_register_skin');
const rulesCheckbox = document.getElementById('checkbox_register_rules');
const registerButton = document.getElementById('btn_register');

document.addEventListener('DOMContentLoaded', function () {
    function validateForm() {
        const fields = [nickname, password, history, how_did_you_find];
        const isFormValid = fields.every(field => field.value.trim() !== '') &&
                            skin.files.length > 0 &&
                            rulesCheckbox.checked;

        registerButton.disabled = !isFormValid;
    }

    // Привязываем событие 'input' ко всем полям для проверки формы в реальном времени
    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);
    history.addEventListener('input', validateForm);
    how_did_you_find.addEventListener('input', validateForm);
    skin.addEventListener('input', validateForm);
    rulesCheckbox.addEventListener('change', validateForm);

    // Начальная проверка формы
    validateForm();
});

async function register_account() {
    try {
        const formData = new FormData();
        formData.append('nickname', nickname.value);
        formData.append('password', password.value);
        formData.append('history', history.value);
        formData.append('how_did_you_find', how_did_you_find.value);
        formData.append('skin', skin.files[0]);  // Отправляем файл

        const result = await window.pywebview.api.account_register(formData);

        if (Array.isArray(result)) {
            if (result[3]) {
                open_tab("index.html");
            } else {
                open_tab("link_discord_register.html");
            }
        } else {
            if (result === 401) {
                showErrorModal("Неверный логин или пароль.");
            } else {
                showErrorModal("Произошла непредвиденная ошибка. Попробуйте еще раз.");
            }
        }
    } catch (error) {
        showErrorModal("Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
}

registerButton.addEventListener("click", function () {
    register_account();
});

document.addEventListener('click', function (event) {
    if (event.target.tagName === 'A' && event.target.href) {
        event.preventDefault();
        window.pywebview.api.open_link(event.target.href);
    }
});
