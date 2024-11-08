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

    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);
    history.addEventListener('input', validateForm);
    how_did_you_find.addEventListener('input', validateForm);
    skin.addEventListener('input', validateForm);
    rulesCheckbox.addEventListener('change', validateForm);

    validateForm();
});

async function register_account() {
    try {
        const skinFile = skin.files[0];

        const reader = new FileReader();
        reader.readAsArrayBuffer(skinFile);
        reader.onloadend = async function () {
            const skinBytes = Array.from(new Uint8Array(reader.result));
            const result = await window.pywebview.api.account_register(
                nickname.value,
                password.value,
                history.value,
                how_did_you_find.value,
                skinBytes
            );

            if (result.status_code === 200) {
                if (result.result[3]) {
                    open_tab("index.html");
                } else {
                    open_tab("link_discord_register.html");
                }

            } else {
                if (result.status_code === 409) {
                    show_info_modal("Ошибка", "Аккаунт с таким ником уже существует")
                } else {
                    show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
                }
            }
        };

    } catch (error) {
        show_info_modal("Ошибка", "Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз.");
        console.error(error);
    }
}

registerButton.addEventListener("click", function () {
    register_account();
});