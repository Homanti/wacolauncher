const nickname = document.getElementById('input_login_nickname');
const password = document.getElementById('input_login_password');
const loginButton = document.getElementById('btn_login');

document.addEventListener('DOMContentLoaded', function () {
    function validateForm() {
        const isFormValid = nickname.value.trim() !== '' &&
                            password.value.trim() !== '';
        loginButton.disabled = !isFormValid;
    }

    nickname.addEventListener('input', validateForm);
    password.addEventListener('input', validateForm);

    validateForm();
});

window.addEventListener('pywebviewready', async function() {
    const accounts = await window.pywebview.api.readJson("data/credentials.json");

    if (accounts.length > 0) {
        document.getElementById("header").style.display = 'block';
    } else {
        document.getElementById("header").style.display = 'none';
    }
});


async function login_account() {
    const result = await window.pywebview.api.account_login(nickname.value, password.value);

    if (result.status_code === 200) {
        if (result.result[3]) {
            open_tab("index.html")
        } else {
            open_tab("link_discord_register.html")
        }
    } else {
        if (result.status_code === 401) {
            show_info_modal("Ошибка", "Неверный логин или пароль.");
        } else {
            show_info_modal("Ошибка", "Произошла непредвиденная ошибка. Попробуйте еще раз.");
        }
    }
}

loginButton.addEventListener("click", function () {
    login_account();
})