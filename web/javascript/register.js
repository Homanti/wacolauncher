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
        const file = skin.files[0];
        const fileReader = new FileReader();

        fileReader.onload = async function(event) {
            const fileBytes = new Uint8Array(event.target.result);
            const result = await window.pywebview.api.account_register(
                nickname.value,
                password.value,
                history.value,
                how_did_you_find.value,
                fileBytes
            );

            if (Array.isArray(result)) {
                if (result[3]) {
                    open_tab("index.html");
                } else {
                    open_tab("link_discord_register.html");
                }
            } else {
                if (result === 401) {
                    show_info_modal("Ошибка", "Неверный логин или пароль.");
                } else {
                    show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
                }
            }
        };

        fileReader.readAsArrayBuffer(file);

    } catch (error) {
        show_info_modal("Ошибка", "Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
}

registerButton.addEventListener("click", function () {
    register_account();
});