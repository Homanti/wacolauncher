const nickname = document.getElementById('input_register_nickname');
const password = document.getElementById('input_register_password');
const history = document.getElementById('input_register_history');
const whereInfo = document.getElementById('input_register_where_info');
const skin = document.getElementById('input_register_skin');
const rulesCheckbox = document.getElementById('checkbox_register_rules');
const registerButton = document.getElementById('btn_register');

document.addEventListener('DOMContentLoaded', function () {
function validateForm() {
    const fields = [nickname, password, history, whereInfo];
    const isFormValid = fields.every(field => field.value.trim() !== '') &&
                        skin.files.length > 0 &&
                        rulesCheckbox.checked;

    registerButton.disabled = !isFormValid;
    }


    // Привязываем событие 'input' ко всем полям для проверки формы в реальном времени
    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);
    history.addEventListener('input', validateForm);
    whereInfo.addEventListener('input', validateForm);
    skin.addEventListener('input', validateForm);
    rulesCheckbox.addEventListener('change', validateForm);

    // Начальная проверка формы
    validateForm();
});

registerButton.addEventListener("click", function () {
    window.pywebview.api.account_register(nickname.value, password.value);
})

document.addEventListener('click', function (event) {
    if (event.target.tagName === 'A' && event.target.href) {
        event.preventDefault();
        window.pywebview.api.open_link(event.target.href);
    }
});
